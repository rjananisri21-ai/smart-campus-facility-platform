from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'department', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active', 'department']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Smart Campus Profile', {'fields': ('role', 'department', 'phone_number')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Smart Campus Profile', {'fields': ('role', 'department', 'phone_number')}),
    )


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'facility_type', 'location', 'capacity', 'status', 'created_at']
    list_filter = ['facility_type', 'status', 'location']
    search_fields = ['name', 'location']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'facility', 'user', 'start_time', 'end_time', 'status', 'created_at']
    list_filter = ['status', 'facility', 'start_time']
    search_fields = ['facility__name', 'user__username', 'purpose']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'facility', 'priority', 'status', 'created_by', 'assigned_to', 'created_at']
    list_filter = ['priority', 'status', 'facility']
    search_fields = ['title', 'description', 'created_by__username']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'author', 'created_at']
    search_fields = ['comment', 'author__username']


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'priority', 'response_time_hours', 'resolution_time_hours', 'is_active']
    list_filter = ['priority', 'is_active']


@admin.register(SensorEvent)
class SensorEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'facility', 'sensor_type', 'metric_value', 'unit', 'recorded_at']
    list_filter = ['sensor_type', 'facility']


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'ticket', 'reviewer', 'status', 'reviewed_at']
    list_filter = ['status', 'reviewer']


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'actor', 'action', 'resource_type', 'resource_id', 'ip_address']
    list_filter = ['action', 'resource_type']
    search_fields = ['action', 'resource_id', 'actor__username']
    readonly_fields = ['created_at']
