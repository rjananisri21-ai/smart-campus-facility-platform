from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    User,
    Facility,
    Booking,
    Ticket,
    Comment,
    SLAPolicy,
    SensorEvent,
    Approval,
    AuditEvent,
)
from .services import (
    create_booking_with_lock,
    approve_booking_with_lock,
    reject_booking_with_lock,
)


class ModelAndConstraintTests(TestCase):
    def setUp(self):
        # 1. User
        self.student = User.objects.create_user(
            username='student1',
            password='Password123!',
            email='student1@campus.edu',
            role=User.ROLE_STUDENT,
            department='Computer Science'
        )
        self.faculty = User.objects.create_user(
            username='faculty1',
            password='Password123!',
            email='faculty1@campus.edu',
            role=User.ROLE_FACULTY,
            department='Physics'
        )
        self.technician = User.objects.create_user(
            username='tech1',
            password='Password123!',
            email='tech1@campus.edu',
            role=User.ROLE_TECHNICIAN,
            department='Maintenance'
        )
        self.admin = User.objects.create_user(
            username='admin1',
            password='Password123!',
            email='admin1@campus.edu',
            role=User.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # 2. Facility
        self.lab = Facility.objects.create(
            name='Computer Lab 101',
            facility_type='Laboratory',
            location='Engineering Block A',
            capacity=40,
            status=Facility.STATUS_AVAILABLE
        )

        # 3. SLA Policy
        self.sla = SLAPolicy.objects.create(
            name='High Priority SLA',
            priority=Ticket.PRIORITY_HIGH,
            response_time_hours=2,
            resolution_time_hours=8
        )

    def test_all_nine_models_instantiation(self):
        now = timezone.now()

        # 3. Booking
        booking = Booking.objects.create(
            facility=self.lab,
            user=self.student,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=4),
            purpose='CS Lab practicals',
            status=Booking.STATUS_PENDING
        )
        self.assertEqual(booking.facility.name, 'Computer Lab 101')
        self.assertEqual(booking.user.username, 'student1')

        # 4. Ticket
        ticket = Ticket.objects.create(
            title='Projector HDMI port damaged',
            description='Projector does not accept HDMI input',
            facility=self.lab,
            created_by=self.student,
            assigned_to=self.technician,
            priority=Ticket.PRIORITY_HIGH,
            status=Ticket.STATUS_ASSIGNED
        )
        self.assertEqual(ticket.facility.id, self.lab.id)

        # 5. Comment
        comment = Comment.objects.create(
            ticket=ticket,
            author=self.technician,
            comment='Inspected unit. Ordered replacement cable.'
        )
        self.assertEqual(comment.ticket.id, ticket.id)

        # 6. SLAPolicy check
        self.assertEqual(self.sla.priority, Ticket.PRIORITY_HIGH)

        # 7. SensorEvent
        event = SensorEvent.objects.create(
            facility=self.lab,
            sensor_type='TEMPERATURE',
            metric_value=Decimal('22.50'),
            unit='°C',
            raw_payload={'source': 'sensor_node_04', 'battery': '98%'}
        )
        self.assertEqual(event.facility.id, self.lab.id)

        # 8. Approval
        approval = Approval.objects.create(
            booking=booking,
            reviewer=self.faculty,
            status=Approval.STATUS_APPROVED,
            remarks='Approved for lab session'
        )
        self.assertEqual(approval.booking.id, booking.id)

        # 9. AuditEvent
        audit = AuditEvent.objects.create(
            actor=self.admin,
            action='FACILITY_UPDATED',
            resource_type='Facility',
            resource_id=str(self.lab.id),
            details={'change': 'status updated to Available'},
            ip_address='127.0.0.1'
        )
        self.assertEqual(audit.actor.username, 'admin1')

        # Assert all 9 models saved and retrieved
        self.assertTrue(User.objects.filter(id=self.student.id).exists())
        self.assertTrue(Facility.objects.filter(id=self.lab.id).exists())
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())
        self.assertTrue(Ticket.objects.filter(id=ticket.id).exists())
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())
        self.assertTrue(SLAPolicy.objects.filter(id=self.sla.id).exists())
        self.assertTrue(SensorEvent.objects.filter(id=event.id).exists())
        self.assertTrue(Approval.objects.filter(id=approval.id).exists())
        self.assertTrue(AuditEvent.objects.filter(id=audit.id).exists())


class BookingConflictAndConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.student_a = User.objects.create_user(
            username='alice',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.student_b = User.objects.create_user(
            username='bob',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.faculty = User.objects.create_user(
            username='prof_smith',
            password='Password123!',
            role=User.ROLE_FACULTY
        )
        self.hall = Facility.objects.create(
            name='Main Auditorium',
            facility_type='Auditorium',
            location='Main Building',
            capacity=500,
            status=Facility.STATUS_AVAILABLE
        )

    def test_overlapping_conflict_prevention(self):
        now = timezone.now() + timedelta(days=2)
        start1 = now.replace(hour=10, minute=0, second=0, microsecond=0)
        end1 = now.replace(hour=12, minute=0, second=0, microsecond=0)

        # Alice successfully books 10:00 - 12:00
        booking1 = create_booking_with_lock(
            facility_id=self.hall.id,
            user=self.student_a,
            start_time=start1,
            end_time=end1,
            purpose='Tech Symposium'
        )
        self.assertEqual(booking1.status, Booking.STATUS_PENDING)

        # Bob attempts overlapping booking: 11:00 - 13:00 (overlaps with 10:00 - 12:00)
        start2 = now.replace(hour=11, minute=0, second=0, microsecond=0)
        end2 = now.replace(hour=13, minute=0, second=0, microsecond=0)

        with self.assertRaises(ValidationError) as ctx:
            create_booking_with_lock(
                facility_id=self.hall.id,
                user=self.student_b,
                start_time=start2,
                end_time=end2,
                purpose='Drama Rehearsal'
            )
        self.assertIn('conflict', str(ctx.exception).lower())

        # Bob attempts another overlapping booking: 09:00 - 10:30 (overlaps with start of 10:00 - 12:00)
        start3 = now.replace(hour=9, minute=0, second=0, microsecond=0)
        end3 = now.replace(hour=10, minute=30, second=0, microsecond=0)

        with self.assertRaises(ValidationError):
            create_booking_with_lock(
                facility_id=self.hall.id,
                user=self.student_b,
                start_time=start3,
                end_time=end3,
                purpose='Choir practice'
            )

        # Non-overlapping booking should SUCCEED: 12:00 - 14:00
        start4 = now.replace(hour=12, minute=0, second=0, microsecond=0)
        end4 = now.replace(hour=14, minute=0, second=0, microsecond=0)

        booking2 = create_booking_with_lock(
            facility_id=self.hall.id,
            user=self.student_b,
            start_time=start4,
            end_time=end4,
            purpose='Robotics Showcase'
        )
        self.assertEqual(booking2.status, Booking.STATUS_PENDING)

    def test_approve_booking_with_lock(self):
        now = timezone.now() + timedelta(days=3)
        start = now.replace(hour=14, minute=0, second=0, microsecond=0)
        end = now.replace(hour=16, minute=0, second=0, microsecond=0)

        booking = create_booking_with_lock(
            facility_id=self.hall.id,
            user=self.student_a,
            start_time=start,
            end_time=end,
            purpose='Guest Lecture'
        )

        updated_booking, approval = approve_booking_with_lock(
            booking_id=booking.id,
            reviewer=self.faculty,
            remarks='Approved for guest lecture.'
        )
        self.assertEqual(updated_booking.status, Booking.STATUS_APPROVED)
        self.assertEqual(approval.status, Approval.STATUS_APPROVED)
        self.assertEqual(approval.reviewer.username, 'prof_smith')


class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin_api',
            password='Password123!',
            role=User.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.student = User.objects.create_user(
            username='student_api',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.faculty = User.objects.create_user(
            username='faculty_api',
            password='Password123!',
            role=User.ROLE_FACULTY
        )
        self.technician = User.objects.create_user(
            username='tech_api',
            password='Password123!',
            role=User.ROLE_TECHNICIAN
        )

        self.facility = Facility.objects.create(
            name='Seminar Hall B',
            facility_type='Hall',
            location='Block B',
            capacity=120,
            status=Facility.STATUS_AVAILABLE
        )

    def test_facility_list_and_create(self):
        # Public / Student can read
        response = self.client.get('/api/facilities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Admin can create new facility
        self.client.force_authenticate(user=self.admin)
        post_data = {
            'name': 'Smart Classroom 301',
            'facility_type': 'Classroom',
            'location': 'Block C',
            'capacity': 60,
            'status': 'Available'
        }
        res = self.client.post('/api/facilities/', post_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Facility.objects.filter(name='Smart Classroom 301').count(), 1)

    def test_booking_create_and_approval_api(self):
        self.client.force_authenticate(user=self.student)
        now = timezone.now() + timedelta(days=5)
        start = (now + timedelta(hours=1)).isoformat()
        end = (now + timedelta(hours=3)).isoformat()

        # Create booking via REST API
        booking_payload = {
            'facility': self.facility.id,
            'start_time': start,
            'end_time': end,
            'purpose': 'Club meeting'
        }
        res = self.client.post('/api/bookings/', booking_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking_id = res.data['id']

        # Faculty approves booking via custom REST action
        self.client.force_authenticate(user=self.faculty)
        approve_res = self.client.post(f'/api/bookings/{booking_id}/approve/', {'remarks': 'Approved'})
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_res.data['booking']['status'], 'Approved')

    def test_ticket_and_comment_api(self):
        self.client.force_authenticate(user=self.student)
        ticket_payload = {
            'title': 'AC not cooling',
            'description': 'Air conditioner is running but not cooling the room',
            'facility': self.facility.id,
            'priority': 'Medium',
            'status': 'New'
        }
        res = self.client.post('/api/tickets/', ticket_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ticket_id = res.data['id']

        # Technician adds comment and updates status
        self.client.force_authenticate(user=self.technician)
        comment_res = self.client.post(f'/api/tickets/{ticket_id}/add_comment/', {'comment': 'Checking gas levels.'})
        self.assertEqual(comment_res.status_code, status.HTTP_201_CREATED)

        patch_res = self.client.patch(f'/api/tickets/{ticket_id}/update_status/', {'status': 'In Progress'})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['status'], 'In Progress')
