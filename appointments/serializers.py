"""
=============================================================================
appointments/serializers.py - Appointment Booking Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Booking
from accounts.models import CustomUser
from etc.validators import validate_future_date


# ======================== Nested User Serializers ========================

class PatientMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal patient info for bookings
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


class DoctorMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal doctor info for bookings
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


# ======================== Booking Serializers ========================

class BookingListSerializer(serializers.ModelSerializer):
    """
    Minimal booking serializer for lists
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'appointment_datetime', 'status', 'status_display',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Detailed booking serializer with full patient and doctor info
    """
    patient_details = PatientMinimalSerializer(source='patient', read_only=True)
    doctor_details = DoctorMinimalSerializer(source='doctor', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'patient', 'patient_details', 'doctor', 'doctor_details',
            'appointment_datetime', 'status', 'status_display',
            'reason', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating bookings
    """

    class Meta:
        model = Booking
        fields = [
            'patient', 'doctor', 'appointment_datetime',
            'reason', 'notes'
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

    def validate_appointment_datetime(self, value):
        """Validate appointment is in the future and during working hours"""
        # Check if in the future
        try:
            validate_future_date(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        # Check if within working hours (8 AM - 8 PM)
        if value.hour < 8 or value.hour >= 20:
            raise serializers.ValidationError(
                "مواعيد الحجز متاحة من 8 صباحاً حتى 8 مساءً / Appointments available from 8 AM to 8 PM"
            )

        # Check if not on Friday (weekend in Egypt)
        if value.weekday() == 4:  # Friday
            raise serializers.ValidationError(
                "لا يمكن الحجز يوم الجمعة / Appointments not available on Fridays"
            )

        return value

    def validate(self, attrs):
        """Validate no conflicts with existing bookings"""
        patient = attrs.get('patient')
        doctor = attrs.get('doctor')
        appointment_datetime = attrs.get('appointment_datetime')

        # Check if patient has another booking on the same day
        booking_date = appointment_datetime.date()
        patient_bookings = Booking.objects.filter(
            patient=patient,
            appointment_datetime__date=booking_date
        ).exclude(status='cancelled')

        if patient_bookings.exists():
            raise serializers.ValidationError({
                'patient': f'المريض لديه حجز آخر في {booking_date} / Patient already has a booking on {booking_date}'
            })

        # Check if doctor is available at this time (30-minute slots)
        start_time = appointment_datetime
        end_time = start_time + timedelta(minutes=30)

        conflicting_bookings = Booking.objects.filter(
            doctor=doctor,
            appointment_datetime__gte=start_time - timedelta(minutes=30),
            appointment_datetime__lt=end_time
        ).exclude(status='cancelled')

        if conflicting_bookings.exists():
            raise serializers.ValidationError({
                'appointment_datetime': 'الطبيب غير متاح في هذا الوقت / Doctor is not available at this time'
            })

        return attrs

    def create(self, validated_data):
        """Create booking with default pending status"""
        validated_data['status'] = 'pending'

        # If patient is creating for themselves, auto-set patient
        request = self.context.get('request')
        if request and request.user.type == 'patient':
            validated_data['patient'] = request.user

        return super().create(validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating bookings
    Staff can update all fields
    Doctors can update status and notes
    Patients can update reason only (for pending bookings)
    """

    class Meta:
        model = Booking
        fields = [
            'appointment_datetime', 'status', 'reason', 'notes'
        ]

    def validate_appointment_datetime(self, value):
        """Validate appointment is in the future and during working hours"""
        if value:
            try:
                validate_future_date(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))

            if value.hour < 8 or value.hour >= 20:
                raise serializers.ValidationError(
                    "مواعيد الحجز متاحة من 8 صباحاً حتى 8 مساءً / Appointments available from 8 AM to 8 PM"
                )

            if value.weekday() == 4:  # Friday
                raise serializers.ValidationError(
                    "لا يمكن الحجز يوم الجمعة / Appointments not available on Fridays"
                )

        return value

    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance

        # Can't change status of cancelled bookings
        if instance.status == 'cancelled':
            raise serializers.ValidationError(
                "لا يمكن تعديل حجز ملغي / Cannot modify cancelled booking"
            )

        # Can't change status of completed bookings
        if instance.status == 'completed':
            raise serializers.ValidationError(
                "لا يمكن تعديل حجز مكتمل / Cannot modify completed booking"
            )

        return value

    def update(self, instance, validated_data):
        """Update booking with role-based restrictions"""
        request = self.context.get('request')

        # Patients can only update reason for pending bookings
        if request and request.user.type == 'patient':
            if instance.status != 'pending':
                raise serializers.ValidationError(
                    "يمكن تعديل الحجوزات قيد الانتظار فقط / Can only modify pending bookings"
                )
            # Only allow reason update
            instance.reason = validated_data.get('reason', instance.reason)
            instance.save()
            return instance

        # Doctors can update status and notes
        if request and request.user.type == 'doctor':
            instance.status = validated_data.get('status', instance.status)
            instance.notes = validated_data.get('notes', instance.notes)
            instance.save()
            return instance

        # Staff can update all fields
        return super().update(instance, validated_data)


class BookingStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating booking status only
    """
    status = serializers.ChoiceField(
        choices=['confirmed', 'completed', 'cancelled'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance

        if instance.status == 'cancelled':
            raise serializers.ValidationError(
                "لا يمكن تعديل حجز ملغي / Cannot modify cancelled booking"
            )

        if instance.status == 'completed':
            raise serializers.ValidationError(
                "لا يمكن تعديل حجز مكتمل / Cannot modify completed booking"
            )

        return value


class BookingCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling bookings
    """
    reason = serializers.CharField(required=False, allow_blank=True)


# ======================== Statistics Serializers ========================

class BookingStatsSerializer(serializers.Serializer):
    """
    Serializer for booking statistics
    """
    total_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    today_bookings = serializers.IntegerField()
    upcoming_bookings = serializers.IntegerField()