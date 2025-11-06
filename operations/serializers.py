"""
=============================================================================
operations/serializers.py - Operations & Media Management Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from .models import Operation, OperationMedia
from accounts.models import CustomUser
from appointments.models import Booking
from etc.validators import validate_positive_number, validate_file_size


# ======================== Nested Serializers ========================

class PatientOperationSerializer(serializers.ModelSerializer):
    """
    Minimal patient info for operations
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


class DoctorOperationSerializer(serializers.ModelSerializer):
    """
    Minimal doctor info for operations
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name']
        read_only_fields = fields


class BookingOperationSerializer(serializers.ModelSerializer):
    """
    Minimal booking info for operations
    """
    appointment_datetime = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'appointment_datetime', 'status']
        read_only_fields = fields


# ======================== Operation Media Serializers ========================

class OperationMediaListSerializer(serializers.ModelSerializer):
    """
    Minimal media serializer for lists
    """
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = OperationMedia
        fields = [
            'id', 'operation', 'media_type', 'media_type_display',
            'file_url', 'file_name', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_file_url(self, obj):
        """Get full URL for file"""
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
            return obj.file_path.url
        return None

    def get_file_name(self, obj):
        """Get original filename"""
        if obj.file_path:
            return obj.file_path.name.split('/')[-1]
        return None


class OperationMediaDetailSerializer(OperationMediaListSerializer):
    """
    Detailed media serializer
    """
    file_size = serializers.SerializerMethodField()

    class Meta(OperationMediaListSerializer.Meta):
        fields = OperationMediaListSerializer.Meta.fields + ['file_size']

    def get_file_size(self, obj):
        """Get file size in MB"""
        if obj.file_path:
            size_bytes = obj.file_path.size
            return round(size_bytes / (1024 * 1024), 2)
        return None


class OperationMediaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading operation media
    """

    class Meta:
        model = OperationMedia
        fields = ['operation', 'media_type', 'file_path', 'description']

    def validate_file_path(self, value):
        """Validate file size"""
        if value:
            try:
                validate_file_size(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        """Validate operation exists and user has permission"""
        operation = attrs.get('operation')
        request = self.context.get('request')

        if operation and request:
            # Check if user is the doctor of this operation or admin
            if request.user.type == 'doctor' and operation.doctor != request.user:
                raise serializers.ValidationError({
                    'operation': 'لا يمكنك إضافة ملفات لعملية ليست لك / Cannot add media to another doctor\'s operation'
                })

        return attrs


# ======================== Operation Serializers ========================

class OperationListSerializer(serializers.ModelSerializer):
    """
    Minimal operation serializer for lists
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    media_count = serializers.SerializerMethodField()

    class Meta:
        model = Operation
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'operation_name', 'cost', 'operation_date', 'status',
            'status_display', 'media_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_media_count(self, obj):
        """Count media files for this operation"""
        return obj.media_files.count()


class OperationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed operation serializer with nested relations
    """
    patient_details = PatientOperationSerializer(source='patient', read_only=True)
    doctor_details = DoctorOperationSerializer(source='doctor', read_only=True)
    booking_details = BookingOperationSerializer(source='booking', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    media_files = OperationMediaListSerializer(many=True, read_only=True)
    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = Operation
        fields = [
            'id', 'patient', 'patient_details', 'doctor', 'doctor_details',
            'booking', 'booking_details', 'operation_name', 'description',
            'procedure_details', 'cost', 'operation_date', 'duration',
            'duration_display', 'status', 'status_display', 'notes',
            'media_files', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_duration_display(self, obj):
        """Format duration as HH:MM"""
        if obj.duration:
            return obj.duration.strftime('%H:%M')
        return None


class OperationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating operations
    """

    class Meta:
        model = Operation
        fields = [
            'patient', 'doctor', 'booking', 'operation_name',
            'description', 'procedure_details', 'cost',
            'operation_date', 'duration', 'status', 'notes'
        ]

    def validate_patient(self, value):
        """Validate patient exists and is active"""
        if value.type != 'patient':
            raise serializers.ValidationError(
                "المستخدم المحدد ليس مريضاً / Selected user is not a patient"
            )
        if not value.is_active:
            raise serializers.ValidationError(
                "حساب المريض غير مفعل / Patient account is inactive"
            )
        return value

    def validate_doctor(self, value):
        """Validate doctor exists and is active"""
        if value.type != 'doctor':
            raise serializers.ValidationError(
                "المستخدم المحدد ليس طبيباً / Selected user is not a doctor"
            )
        if not value.is_active:
            raise serializers.ValidationError(
                "حساب الطبيب غير مفعل / Doctor account is inactive"
            )
        return value

    def validate_cost(self, value):
        """Validate cost is positive"""
        if value < 0:
            raise serializers.ValidationError(
                "التكلفة لا يمكن أن تكون سالبة / Cost cannot be negative"
            )
        return value

    def validate_operation_date(self, value):
        """Validate operation date"""
        from django.utils import timezone
        if value > timezone.now().date():
            # Allow future dates for scheduled operations
            pass
        return value

    def validate(self, attrs):
        """Validate booking belongs to patient if provided"""
        booking = attrs.get('booking')
        patient = attrs.get('patient')

        if booking:
            if booking.patient != patient:
                raise serializers.ValidationError({
                    'booking': 'الحجز لا يخص هذا المريض / Booking does not belong to this patient'
                })

            # Check if booking already has an operation
            if hasattr(booking, 'operation') and booking.operation:
                # If updating, allow same operation
                instance = self.instance
                if not instance or booking.operation != instance:
                    raise serializers.ValidationError({
                        'booking': 'هذا الحجز مرتبط بعملية أخرى بالفعل / Booking already linked to another operation'
                    })

        return attrs

    def create(self, validated_data):
        """Create operation with doctor from context if not provided"""
        request = self.context.get('request')

        # If doctor is current user and not specified, auto-set
        if request and request.user.type == 'doctor' and 'doctor' not in validated_data:
            validated_data['doctor'] = request.user

        return super().create(validated_data)


class OperationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating operations
    Cannot change patient or doctor, only operation details
    """

    class Meta:
        model = Operation
        fields = [
            'operation_name', 'description', 'procedure_details',
            'cost', 'operation_date', 'duration', 'status', 'notes'
        ]

    def validate_cost(self, value):
        """Validate cost is positive"""
        if value < 0:
            raise serializers.ValidationError(
                "التكلفة لا يمكن أن تكون سالبة / Cost cannot be negative"
            )
        return value

    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance

        # Cannot change from completed/cancelled to other statuses
        if instance.status == 'completed' and value != 'completed':
            raise serializers.ValidationError(
                "لا يمكن تغيير حالة عملية مكتملة / Cannot change status of completed operation"
            )

        if instance.status == 'cancelled' and value != 'cancelled':
            raise serializers.ValidationError(
                "لا يمكن تغيير حالة عملية ملغية / Cannot change status of cancelled operation"
            )

        return value


class OperationStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating operation status only
    """
    status = serializers.ChoiceField(
        choices=['scheduled', 'in_progress', 'completed', 'cancelled'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)


# ======================== Statistics Serializers ========================

class OperationStatsSerializer(serializers.Serializer):
    """
    Serializer for operation statistics
    """
    total_operations = serializers.IntegerField()
    scheduled_operations = serializers.IntegerField()
    in_progress_operations = serializers.IntegerField()
    completed_operations = serializers.IntegerField()
    cancelled_operations = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_operations = serializers.IntegerField()
    this_month_operations = serializers.IntegerField()


class DoctorOperationStatsSerializer(serializers.Serializer):
    """
    Serializer for doctor-specific operation statistics
    """
    doctor_id = serializers.IntegerField()
    doctor_name = serializers.CharField()
    total_operations = serializers.IntegerField()
    completed_operations = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class OperationTypeStatsSerializer(serializers.Serializer):
    """
    Serializer for operation type statistics
    """
    operation_name = serializers.CharField()
    count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_cost = serializers.DecimalField(max_digits=10, decimal_places=2)