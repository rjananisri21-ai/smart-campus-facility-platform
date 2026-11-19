from rest_framework import serializers
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
from .services import create_booking_with_lock


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'department',
            'phone_number',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'email',
            'first_name',
            'last_name',
            'role',
            'department',
            'phone_number',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FacilitySerializer(serializers.ModelSerializer):
    active_bookings_count = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = [
            'id',
            'name',
            'facility_type',
            'location',
            'capacity',
            'status',
            'description',
            'active_bookings_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_active_bookings_count(self, obj):
        return obj.bookings.filter(status__in=[Booking.STATUS_PENDING, Booking.STATUS_APPROVED]).count()


class BookingSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.name')
    facility_location = serializers.ReadOnlyField(source='facility.location')
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Booking
        fields = [
            'id',
            'facility',
            'facility_name',
            'facility_location',
            'user',
            'user_name',
            'start_time',
            'end_time',
            'purpose',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "Booking end time must be after start time."})
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if (request and request.user.is_authenticated) else validated_data.get('user')
        if not user or not user.is_authenticated:
            # Fallback for development/testing if unauthenticated user is passed
            user = User.objects.filter(is_superuser=True).first() or User.objects.first()

        facility = validated_data['facility']
        start_time = validated_data['start_time']
        end_time = validated_data['end_time']
        purpose = validated_data.get('purpose', '')

        # Use our concurrency-safe row-locking service
        return create_booking_with_lock(
            facility_id=facility.id,
            user=user,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            request=request
        )


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'ticket', 'author', 'author_name', 'comment', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        elif 'author' not in validated_data:
            validated_data['author'] = User.objects.first()
        return super().create(validated_data)


class TicketSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.username')
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'title',
            'description',
            'facility',
            'facility_name',
            'location_custom',
            'created_by',
            'created_by_name',
            'assigned_to',
            'assigned_to_name',
            'priority',
            'status',
            'comments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        elif 'created_by' not in validated_data:
            validated_data['created_by'] = User.objects.first()
        return super().create(validated_data)


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = '__all__'


class SensorEventSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.name')

    class Meta:
        model = SensorEvent
        fields = [
            'id',
            'facility',
            'facility_name',
            'sensor_type',
            'metric_value',
            'unit',
            'recorded_at',
            'raw_payload',
        ]
        read_only_fields = ['id', 'recorded_at']


class ApprovalSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.ReadOnlyField(source='reviewer.username')
    facility_name = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = [
            'id',
            'booking',
            'ticket',
            'reviewer',
            'reviewer_name',
            'status',
            'remarks',
            'facility_name',
            'reviewed_at',
        ]
        read_only_fields = ['id', 'reviewer', 'reviewed_at']

    def get_facility_name(self, obj):
        if obj.booking and obj.booking.facility:
            return obj.booking.facility.name
        if obj.ticket and obj.ticket.facility:
            return obj.ticket.facility.name
        return ''


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source='actor.username')

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'actor',
            'actor_name',
            'action',
            'resource_type',
            'resource_id',
            'details',
            'ip_address',
            'created_at',
        ]
        read_only_fields = '__all__'
