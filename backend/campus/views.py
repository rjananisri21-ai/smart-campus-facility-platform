from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

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
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    FacilitySerializer,
    BookingSerializer,
    TicketSerializer,
    CommentSerializer,
    SLAPolicySerializer,
    SensorEventSerializer,
    ApprovalSerializer,
    AuditEventSerializer,
)
from .permissions import (
    IsAdminRole,
    IsFacultyOrAdmin,
    IsTechnicianOrAdmin,
    FacilityPermission,
    BookingPermission,
    TicketPermission,
)
from .services import (
    approve_booking_with_lock,
    reject_booking_with_lock,
)


# -----------------------------------------------------------------------------
# User & Auth Views
# -----------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return Response({
            'message': 'Logged in successfully',
            'user': UserSerializer(user).data
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def current_user(request):
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)


# -----------------------------------------------------------------------------
# Facility ViewSet
# -----------------------------------------------------------------------------
class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().prefetch_related('bookings')
    serializer_class = FacilitySerializer
    permission_classes = [FacilityPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        facility_type = self.request.query_params.get('type')
        search = self.request.query_params.get('search')
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        if facility_type:
            qs = qs.filter(facility_type__icontains=facility_type)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


# -----------------------------------------------------------------------------
# Booking ViewSet (with Conflict Prevention & Row Locking)
# -----------------------------------------------------------------------------
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('facility', 'user').all()
    serializer_class = BookingSerializer
    permission_classes = [BookingPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs

        # Regular students see only their own bookings; Faculty and Admins see all
        if user.role == User.ROLE_STUDENT:
            qs = qs.filter(user=user)

        facility_id = self.request.query_params.get('facility')
        status_param = self.request.query_params.get('status')
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        return qs

    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as exc:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    @action(detail=True, methods=['post'], permission_classes=[IsFacultyOrAdmin])
    def approve(self, request, pk=None):
        remarks = request.data.get('remarks', 'Approved by authorized faculty/admin.')
        try:
            booking, approval = approve_booking_with_lock(
                booking_id=pk,
                reviewer=request.user,
                remarks=remarks,
                request=request
            )
            return Response({
                'message': 'Booking approved successfully',
                'booking': BookingSerializer(booking).data,
                'approval': ApprovalSerializer(approval).data
            })
        except DjangoValidationError as exc:
            return Response(
                {'error': exc.messages if hasattr(exc, 'messages') else str(exc)},
                status=status.HTTP_409_CONFLICT
            )

    @action(detail=True, methods=['post'], permission_classes=[IsFacultyOrAdmin])
    def reject(self, request, pk=None):
        remarks = request.data.get('remarks', 'Rejected by authorized faculty/admin.')
        try:
            booking, approval = reject_booking_with_lock(
                booking_id=pk,
                reviewer=request.user,
                remarks=remarks,
                request=request
            )
            return Response({
                'message': 'Booking rejected',
                'booking': BookingSerializer(booking).data,
                'approval': ApprovalSerializer(approval).data
            })
        except DjangoValidationError as exc:
            return Response(
                {'error': exc.messages if hasattr(exc, 'messages') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        AuditEvent.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            action='BOOKING_CANCELLED',
            resource_type='Booking',
            resource_id=str(booking.id),
            details={'reason': request.data.get('reason', 'Cancelled by user')}
        )
        return Response({'message': 'Booking cancelled', 'booking': BookingSerializer(booking).data})


# -----------------------------------------------------------------------------
# Ticket ViewSet (Maintenance Requests)
# -----------------------------------------------------------------------------
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('facility', 'created_by', 'assigned_to').prefetch_related('comments').all()
    serializer_class = TicketSerializer
    permission_classes = [TicketPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs

        if user.role == User.ROLE_STUDENT:
            qs = qs.filter(created_by=user)
        elif user.role == User.ROLE_TECHNICIAN:
            assigned_only = self.request.query_params.get('assigned_only')
            if assigned_only == 'true':
                qs = qs.filter(assigned_to=user)

        status_param = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        if priority:
            qs = qs.filter(priority__iexact=priority)
        return qs

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        comment_text = request.data.get('comment')
        if not comment_text:
            return Response({'error': 'Comment body is required'}, status=status.HTTP_400_BAD_REQUEST)

        author = request.user if request.user.is_authenticated else User.objects.first()
        comment = Comment.objects.create(ticket=ticket, author=author, comment=comment_text)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], permission_classes=[IsTechnicianOrAdmin])
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        assigned_to_id = request.data.get('assigned_to')

        if new_status:
            ticket.status = new_status
        if assigned_to_id:
            ticket.assigned_to_id = assigned_to_id
        ticket.save()

        AuditEvent.objects.create(
            actor=request.user,
            action='TICKET_STATUS_UPDATED',
            resource_type='Ticket',
            resource_id=str(ticket.id),
            details={'new_status': ticket.status, 'assigned_to': ticket.assigned_to_id}
        )
        return Response(TicketSerializer(ticket).data)


# -----------------------------------------------------------------------------
# Additional ViewSets: Comments, SLA, SensorEvents, Approvals, Audit
# -----------------------------------------------------------------------------
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('ticket', 'author').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SLAPolicyViewSet(viewsets.ModelViewSet):
    queryset = SLAPolicy.objects.all()
    serializer_class = SLAPolicySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SensorEventViewSet(viewsets.ModelViewSet):
    queryset = SensorEvent.objects.select_related('facility').all()
    serializer_class = SensorEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ApprovalViewSet(viewsets.ModelViewSet):
    queryset = Approval.objects.select_related('booking', 'ticket', 'reviewer').all()
    serializer_class = ApprovalSerializer
    permission_classes = [IsFacultyOrAdmin]


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related('actor').all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsAdminRole]
