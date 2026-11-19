from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from campus.models import (
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


class Command(BaseCommand):
    help = 'Seeds initial campus data matching the Smart Campus frontend'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Smart Campus database...")

        # 1. Users
        users = [
            {'username': 'admin', 'email': 'admin@campus.edu', 'role': User.ROLE_ADMIN, 'is_staff': True, 'is_superuser': True},
            {'username': 'Janani', 'email': 'janani@campus.edu', 'role': User.ROLE_STUDENT, 'department': 'Computer Science'},
            {'username': 'Arun', 'email': 'arun@campus.edu', 'role': User.ROLE_STUDENT, 'department': 'Electronics'},
            {'username': 'prof_kumar', 'email': 'pkumar@campus.edu', 'role': User.ROLE_FACULTY, 'department': 'Information Tech'},
            {'username': 'tech_ravi', 'email': 'ravi@campus.edu', 'role': User.ROLE_TECHNICIAN, 'department': 'Campus Maintenance'},
        ]

        user_objs = {}
        for u in users:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'role': u['role'],
                    'department': u.get('department', ''),
                    'is_staff': u.get('is_staff', False),
                    'is_superuser': u.get('is_superuser', False),
                }
            )
            if created:
                user.set_password('Campus@123')
                user.save()
            user_objs[u['username']] = user
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(user_objs)} users."))

        # 2. Facilities
        facilities = [
            {'name': 'Computer Lab 1', 'facility_type': 'Laboratory', 'location': 'Block A', 'capacity': 40, 'status': 'Available'},
            {'name': 'Seminar Hall', 'facility_type': 'Hall', 'location': 'Block B', 'capacity': 120, 'status': 'Available'},
            {'name': 'Smart Classroom', 'facility_type': 'Classroom', 'location': 'Block C', 'capacity': 60, 'status': 'Available'},
            {'name': 'Physics Lab', 'facility_type': 'Laboratory', 'location': 'Block D', 'capacity': 30, 'status': 'Maintenance'},
        ]
        facility_objs = {}
        for f in facilities:
            fac, _ = Facility.objects.get_or_create(
                name=f['name'],
                defaults=f
            )
            facility_objs[f['name']] = fac
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(facility_objs)} facilities."))

        # 3. SLA Policies
        sla_rules = [
            {'name': 'Critical SLA', 'priority': 'Critical', 'response_time_hours': 1, 'resolution_time_hours': 4},
            {'name': 'High Priority SLA', 'priority': 'High', 'response_time_hours': 2, 'resolution_time_hours': 8},
            {'name': 'Medium Priority SLA', 'priority': 'Medium', 'response_time_hours': 8, 'resolution_time_hours': 24},
            {'name': 'Low Priority SLA', 'priority': 'Low', 'response_time_hours': 24, 'resolution_time_hours': 72},
        ]
        for rule in sla_rules:
            SLAPolicy.objects.get_or_create(
                priority=rule['priority'],
                defaults=rule
            )
        self.stdout.write(self.style.SUCCESS("Loaded SLA Policies."))

        # 4. Bookings
        now = timezone.now()
        b1, _ = Booking.objects.get_or_create(
            facility=facility_objs['Computer Lab 1'],
            user=user_objs['Janani'],
            start_time=now + timedelta(days=1, hours=10),
            end_time=now + timedelta(days=1, hours=12),
            defaults={'purpose': 'AI Lab Session', 'status': 'Approved'}
        )
        b2, _ = Booking.objects.get_or_create(
            facility=facility_objs['Seminar Hall'],
            user=user_objs['Arun'],
            start_time=now + timedelta(days=2, hours=14),
            end_time=now + timedelta(days=2, hours=16),
            defaults={'purpose': 'Technical Seminar', 'status': 'Pending'}
        )
        self.stdout.write(self.style.SUCCESS("Loaded initial bookings."))

        # 5. Tickets & Comments
        t1, _ = Ticket.objects.get_or_create(
            title='Projector not working',
            facility=facility_objs['Seminar Hall'],
            defaults={
                'description': 'Projector lamp is blinking red and not displaying HDMI feed',
                'created_by': user_objs['Janani'],
                'priority': 'High',
                'status': 'New'
            }
        )
        t2, _ = Ticket.objects.get_or_create(
            title='Air conditioner issue',
            facility=facility_objs['Computer Lab 1'],
            defaults={
                'description': 'AC unit 2 leaking water',
                'created_by': user_objs['Arun'],
                'assigned_to': user_objs['tech_ravi'],
                'priority': 'Medium',
                'status': 'Assigned'
            }
        )

        Comment.objects.get_or_create(
            ticket=t2,
            author=user_objs['tech_ravi'],
            defaults={'comment': 'Drain line checked, waiting on filter replacement.'}
        )

        # 6. Sensor Event
        SensorEvent.objects.get_or_create(
            facility=facility_objs['Computer Lab 1'],
            sensor_type='TEMPERATURE',
            metric_value=Decimal('23.40'),
            defaults={'unit': '°C', 'raw_payload': {'sensor_id': 'DHT22_LAB1', 'humidity': 55}}
        )

        # 7. Approval
        Approval.objects.get_or_create(
            booking=b1,
            reviewer=user_objs['prof_kumar'],
            defaults={'status': 'Approved', 'remarks': 'Approved for practical lab work'}
        )

        # 8. Audit Event
        AuditEvent.objects.get_or_create(
            action='SYSTEM_INITIALIZED',
            resource_type='Platform',
            resource_id='1',
            defaults={'details': {'seed': 'initial_setup_complete'}}
        )

        self.stdout.write(self.style.SUCCESS("Smart Campus initial seed complete!"))
