from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Facility, Booking, Approval, AuditEvent


def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@transaction.atomic
def create_booking_with_lock(facility_id, user, start_time, end_time, purpose='', request=None):
    """
    Safely creates a booking with row-level locking on the facility to prevent
    concurrent race conditions and double-booking overlaps.
    """
    if end_time <= start_time:
        raise ValidationError({'end_time': "End time must be strictly after start time."})

    # Acquire an exclusive InnoDB row lock on the facility: SELECT ... FOR UPDATE
    # Any concurrent transaction trying to book this facility will block until this completes.
    try:
        facility = Facility.objects.select_for_update().get(id=facility_id)
    except Facility.DoesNotExist:
        raise ValidationError({'facility': "Selected facility does not exist."})

    if facility.status != Facility.STATUS_AVAILABLE:
        raise ValidationError({'facility': f"Facility '{facility.name}' is currently {facility.status} and cannot be booked."})

    # Conflict check: Overlap condition [start_time, end_time) with [b.start_time, b.end_time)
    conflicts = Booking.objects.filter(
        facility=facility,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_APPROVED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )

    if conflicts.exists():
        conflict = conflicts.first()
        start_str = conflict.start_time.strftime('%Y-%m-%d %H:%M')
        end_str = conflict.end_time.strftime('%Y-%m-%d %H:%M')
        raise ValidationError({
            'conflict': f"Time slot conflict: Facility '{facility.name}' already has a {conflict.status} booking from {start_str} to {end_str}."
        })

    booking = Booking.objects.create(
        facility=facility,
        user=user,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        status=Booking.STATUS_PENDING,
    )

    AuditEvent.objects.create(
        actor=user,
        action='BOOKING_CREATED',
        resource_type='Booking',
        resource_id=str(booking.id),
        details={
            'facility_id': facility.id,
            'facility_name': facility.name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'purpose': purpose,
        },
        ip_address=get_client_ip(request)
    )

    return booking


@transaction.atomic
def approve_booking_with_lock(booking_id, reviewer, remarks='', request=None):
    """
    Approves a booking within an atomic transaction with row locking,
    re-validating that no concurrent approved reservation conflicts with it.
    """
    try:
        booking = Booking.objects.select_for_update().get(id=booking_id)
    except Booking.DoesNotExist:
        raise ValidationError({'booking': "Booking not found."})

    facility = Facility.objects.select_for_update().get(id=booking.facility_id)

    # Re-verify no other Approved booking occupies this slot
    conflicts = Booking.objects.filter(
        facility=facility,
        status=Booking.STATUS_APPROVED,
        start_time__lt=booking.end_time,
        end_time__gt=booking.start_time,
    ).exclude(id=booking.id)

    if conflicts.exists():
        conflict = conflicts.first()
        raise ValidationError({
            'conflict': f"Cannot approve: An approved booking already exists from {conflict.start_time} to {conflict.end_time}."
        })

    booking.status = Booking.STATUS_APPROVED
    booking.save(update_fields=['status', 'updated_at'])

    approval = Approval.objects.create(
        booking=booking,
        reviewer=reviewer,
        status=Approval.STATUS_APPROVED,
        remarks=remarks,
    )

    AuditEvent.objects.create(
        actor=reviewer,
        action='BOOKING_APPROVED',
        resource_type='Booking',
        resource_id=str(booking.id),
        details={'remarks': remarks, 'approval_id': approval.id},
        ip_address=get_client_ip(request)
    )

    return booking, approval


@transaction.atomic
def reject_booking_with_lock(booking_id, reviewer, remarks='', request=None):
    try:
        booking = Booking.objects.select_for_update().get(id=booking_id)
    except Booking.DoesNotExist:
        raise ValidationError({'booking': "Booking not found."})

    booking.status = Booking.STATUS_REJECTED
    booking.save(update_fields=['status', 'updated_at'])

    approval = Approval.objects.create(
        booking=booking,
        reviewer=reviewer,
        status=Approval.STATUS_REJECTED,
        remarks=remarks,
    )

    AuditEvent.objects.create(
        actor=reviewer,
        action='BOOKING_REJECTED',
        resource_type='Booking',
        resource_id=str(booking.id),
        details={'remarks': remarks, 'approval_id': approval.id},
        ip_address=get_client_ip(request)
    )

    return booking, approval
