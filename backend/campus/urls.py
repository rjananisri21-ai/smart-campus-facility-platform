from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    FacilityViewSet,
    BookingViewSet,
    TicketViewSet,
    CommentViewSet,
    SLAPolicyViewSet,
    SensorEventViewSet,
    ApprovalViewSet,
    AuditEventViewSet,
    register_user,
    login_user,
    logout_user,
    current_user,
)

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'sla-policies', SLAPolicyViewSet, basename='slapolicy')
router.register(r'sensor-events', SensorEventViewSet, basename='sensorevent')
router.register(r'approvals', ApprovalViewSet, basename='approval')
router.register(r'audit-events', AuditEventViewSet, basename='auditevent')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/register/', register_user, name='auth-register'),
    path('auth/login/', login_user, name='auth-login'),
    path('auth/logout/', logout_user, name='auth-logout'),
    path('auth/me/', current_user, name='auth-me'),
    path('', include(router.urls)),
]
