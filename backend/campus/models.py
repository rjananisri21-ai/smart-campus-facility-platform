from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.utils import timezone


# -----------------------------------------------------------------------------
# 1. User Model (Role-Based: Student, Faculty, Technician, Admin)
# -----------------------------------------------------------------------------
class User(AbstractUser):
    ROLE_STUDENT = 'STUDENT'
    ROLE_FACULTY = 'FACULTY'
    ROLE_TECHNICIAN = 'TECHNICIAN'
    ROLE_ADMIN = 'ADMIN'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_FACULTY, 'Faculty'),
        (ROLE_TECHNICIAN, 'Technician'),
        (ROLE_ADMIN, 'Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        db_index=True,
        help_text="Role-based permission level"
    )
    department = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'campus_users'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_faculty(self):
        return self.role == self.ROLE_FACULTY

    @property
    def is_technician(self):
        return self.role == self.ROLE_TECHNICIAN

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser


# -----------------------------------------------------------------------------
# 2. Facility Model
# -----------------------------------------------------------------------------
class Facility(models.Model):
    STATUS_AVAILABLE = 'Available'
    STATUS_MAINTENANCE = 'Maintenance'
    STATUS_OCCUPIED = 'Occupied'
    STATUS_INACTIVE = 'Inactive'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_MAINTENANCE, 'Maintenance'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    name = models.CharField(max_length=150, unique=True, db_index=True)
    facility_type = models.CharField(max_length=50, help_text="e.g. Laboratory, Hall, Classroom")
    location = models.CharField(max_length=150, help_text="e.g. Block A, Block B")
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_index=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campus_facilities'
        ordering = ['name']
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return f"{self.name} ({self.facility_type}) - {self.location}"


# -----------------------------------------------------------------------------
# 3. Booking Model
# -----------------------------------------------------------------------------
class Booking(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    purpose = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campus_bookings'
        ordering = ['-start_time']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F('start_time')),
                name='booking_end_time_after_start_time'
            )
        ]
        indexes = [
            models.Index(fields=['facility', 'start_time', 'end_time', 'status'], name='idx_bk_fac_time_stat')
        ]

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': "Booking end time must be strictly after start time."})

    def __str__(self):
        return f"Booking #{self.id} - {self.facility.name} by {self.user.username} ({self.status})"


# -----------------------------------------------------------------------------
# 4. Ticket Model (Maintenance Ticket)
# -----------------------------------------------------------------------------
class Ticket(models.Model):
    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    PRIORITY_CRITICAL = 'Critical'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    STATUS_NEW = 'New'
    STATUS_ASSIGNED = 'Assigned'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'
    STATUS_CLOSED = 'Closed'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=200, help_text="Issue description")
    description = models.TextField(blank=True, default='')
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tickets'
    )
    location_custom = models.CharField(max_length=150, blank=True, default='', help_text="Location if not bound to facility")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campus_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id}: {self.title} [{self.priority} / {self.status}]"


# -----------------------------------------------------------------------------
# 5. Comment Model (Ticket Discussion / Updates)
# -----------------------------------------------------------------------------
class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'campus_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Ticket #{self.ticket_id}"


# -----------------------------------------------------------------------------
# 6. SLAPolicy Model (Resolution SLAs)
# -----------------------------------------------------------------------------
class SLAPolicy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    priority = models.CharField(
        max_length=20,
        choices=Ticket.PRIORITY_CHOICES,
        unique=True,
        db_index=True
    )
    response_time_hours = models.PositiveIntegerField(help_text="Expected maximum response time in hours")
    resolution_time_hours = models.PositiveIntegerField(help_text="Expected maximum resolution time in hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campus_sla_policies'
        verbose_name_plural = 'SLA Policies'
        ordering = ['priority']

    def __str__(self):
        return f"SLA Policy: {self.name} ({self.priority}) - {self.resolution_time_hours}h"


# -----------------------------------------------------------------------------
# 7. SensorEvent Model (IoT Smart Campus Telemetry)
# -----------------------------------------------------------------------------
class SensorEvent(models.Model):
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='sensor_events'
    )
    sensor_type = models.CharField(max_length=50, db_index=True, help_text="e.g. OCCUPANCY, TEMPERATURE, POWER")
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, blank=True, default='', help_text="e.g. °C, count, kWh")
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    raw_payload = models.JSONField(blank=True, default=dict)

    class Meta:
        db_table = 'campus_sensor_events'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['facility', 'sensor_type', 'recorded_at'], name='idx_se_fac_typ_rec')
        ]

    def __str__(self):
        return f"{self.sensor_type} @ {self.facility.name}: {self.metric_value} {self.unit}"


# -----------------------------------------------------------------------------
# 8. Approval Model (Booking and Ticket Approvals)
# -----------------------------------------------------------------------------
class Approval(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approvals'
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approvals'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    remarks = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campus_approvals'
        ordering = ['-reviewed_at']

    def __str__(self):
        target = f"Booking #{self.booking_id}" if self.booking_id else f"Ticket #{self.ticket_id}"
        return f"Approval for {target} by {self.reviewer.username}: {self.status}"


# -----------------------------------------------------------------------------
# 9. AuditEvent Model (System Audit Trail)
# -----------------------------------------------------------------------------
class AuditEvent(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    action = models.CharField(max_length=100, db_index=True, help_text="e.g. BOOKING_CREATE, BOOKING_APPROVE")
    resource_type = models.CharField(max_length=50, db_index=True, help_text="e.g. Facility, Booking, Ticket")
    resource_id = models.CharField(max_length=50, blank=True, default='')
    details = models.JSONField(blank=True, default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'campus_audit_events'
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'SYSTEM'
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {actor_name} -> {self.action} on {self.resource_type}:{self.resource_id}"
