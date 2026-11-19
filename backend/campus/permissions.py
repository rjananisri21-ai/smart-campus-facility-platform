from rest_framework import permissions
from .models import User


class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to Admin users (or superusers).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.ROLE_ADMIN or request.user.is_superuser or request.user.is_staff)
        )


class IsFacultyOrAdmin(permissions.BasePermission):
    """
    Allows access to Faculty and Admin users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.ROLE_FACULTY, User.ROLE_ADMIN] or request.user.is_superuser)
        )


class IsTechnicianOrAdmin(permissions.BasePermission):
    """
    Allows access to Technicians and Admins.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.ROLE_TECHNICIAN, User.ROLE_ADMIN] or request.user.is_superuser)
        )


class FacilityPermission(permissions.BasePermission):
    """
    Read access: Anyone authenticated or anonymous.
    Write access: Admin only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.ROLE_ADMIN or request.user.is_superuser)
        )


class BookingPermission(permissions.BasePermission):
    """
    Custom permissions for Bookings:
    - Any authenticated user can create or view their own bookings.
    - Faculty and Admins can view all bookings and perform approvals.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return request.method in permissions.SAFE_METHODS
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in [User.ROLE_ADMIN, User.ROLE_FACULTY] or request.user.is_superuser:
            return True
        return obj.user_id == request.user.id


class TicketPermission(permissions.BasePermission):
    """
    Custom permissions for Maintenance Tickets:
    - Anyone authenticated can report a ticket.
    - Technicians and Admins can update status, priority, and assignments.
    - Regular users can view their own tickets; Technicians/Admins view all.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return request.method in permissions.SAFE_METHODS
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in [User.ROLE_ADMIN, User.ROLE_TECHNICIAN] or request.user.is_superuser:
            return True
        return obj.created_by_id == request.user.id
