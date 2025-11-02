"""
=============================================================================
pharmacy/serializers.py - Pharmacy & Prescription Management Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import MedicineLibrary, Prescription, PrescriptionItem
from accounts.models import CustomUser
from appointments.models import Booking


# ======================== Nested User Serializers ========================

class PatientPrescriptionSerializer(serializers.ModelSerializer):
    """
    Minimal patient info for prescriptions
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


class DoctorPrescriptionSerializer(serializers.ModelSerializer):
    """
    Minimal doctor info for prescriptions
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name']
        read_only_fields = fields


# ======================== Medicine Library Serializers ========================

class MedicineListSerializer(serializers.ModelSerializer):
    """
    Minimal medicine serializer for lists
    """
    form_display = serializers.CharField(source='get_form_display', read_only=True)

    class Meta:
        model = MedicineLibrary
        fields = [
            'id', 'trade_name', 'active_ingredient', 'strength',
            'form', 'form_display', 'times_prescribed', 'created_at'
        ]
        read_only_fields = ['id', 'times_prescribed', 'created_at']


class MedicineDetailSerializer(serializers.ModelSerializer):
    """
    Detailed medicine serializer
    """
    form_display = serializers.CharField(source='get_form_display', read_only=True)

    class Meta:
        model = MedicineLibrary
        fields = [
            'id', 'trade_name', 'active_ingredient', 'strength',
            'form', 'form_display', 'description', 'indications',
            'contraindications', 'side_effects', 'times_prescribed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'times_prescribed', 'created_at', 'updated_at']


class MedicineCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating medicines
    """

    class Meta:
        model = MedicineLibrary
        fields = [
            'trade_name', 'active_ingredient', 'strength', 'form',
            'description', 'indications', 'contraindications', 'side_effects'
        ]

    def validate_trade_name(self, value):
        """Validate trade name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "اسم الدواء يجب أن يكون حرفين على الأقل / Trade name must be at least 2 characters"
            )
        return value.strip()

    def validate_active_ingredient(self, value):
        """Validate active ingredient"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "المادة الفعالة يجب أن تكون حرفين على الأقل / Active ingredient must be at least 2 characters"
            )
        return value.strip()

    def validate_strength(self, value):
        """Validate strength format"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError(
                "القوة مطلوبة / Strength is required"
            )
        return value.strip()

    def validate(self, attrs):
        """Check for duplicate medicine"""
        trade_name = attrs.get('trade_name')
        strength = attrs.get('strength')

        # Check if updating
        instance = self.instance

        if trade_name and strength:
            existing = MedicineLibrary.objects.filter(
                trade_name__iexact=trade_name,
                strength=strength
            )
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'trade_name': f'دواء بنفس الاسم والقوة موجود بالفعل / Medicine with same name and strength already exists'
                })

        return attrs


# ======================== Prescription Item Serializers ========================

class PrescriptionItemSerializer(serializers.ModelSerializer):
    """
    Prescription item with medicine details
    """
    medicine_details = MedicineListSerializer(source='medicine', read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'medicine', 'medicine_details', 'dosage',
            'frequency', 'duration_days', 'instructions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating prescription items
    """

    class Meta:
        model = PrescriptionItem
        fields = ['medicine', 'dosage', 'frequency', 'duration_days', 'instructions']

    def validate_dosage(self, value):
        """Validate dosage format"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "الجرعة مطلوبة / Dosage is required"
            )
        return value.strip()

    def validate_frequency(self, value):
        """Validate frequency"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "التكرار مطلوب / Frequency is required"
            )
        return value.strip()

    def validate_duration_days(self, value):
        """Validate duration is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "المدة يجب أن تكون أكبر من صفر / Duration must be greater than zero"
            )
        if value > 365:
            raise serializers.ValidationError(
                "المدة لا يمكن أن تتجاوز 365 يوم / Duration cannot exceed 365 days"
            )
        return value


# ======================== Prescription Serializers ========================

class PrescriptionListSerializer(serializers.ModelSerializer):
    """
    Minimal prescription serializer for lists
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'prescription_date', 'items_count', 'created_at'
        ]
        read_only_fields = ['id', 'prescription_date', 'created_at']

    def get_items_count(self, obj):
        """Count prescription items"""
        return obj.items.count()


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed prescription serializer with items
    """
    patient_details = PatientPrescriptionSerializer(source='patient', read_only=True)
    doctor_details = DoctorPrescriptionSerializer(source='doctor', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_details', 'doctor', 'doctor_details',
            'booking', 'prescription_date', 'diagnosis', 'instructions',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'prescription_date', 'created_at', 'updated_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating prescriptions with items
    """
    items = PrescriptionItemCreateSerializer(many=True, required=True)

    class Meta:
        model = Prescription
        fields = ['patient', 'booking', 'diagnosis', 'instructions', 'items']

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

    def validate_items(self, value):
        """Validate at least one item"""
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "يجب إضافة دواء واحد على الأقل / At least one medicine is required"
            )
        return value

    def validate(self, attrs):
        """Validate booking belongs to patient if provided"""
        booking = attrs.get('booking')
        patient = attrs.get('patient')

        if booking and booking.patient != patient:
            raise serializers.ValidationError({
                'booking': 'الحجز لا يخص هذا المريض / Booking does not belong to this patient'
            })

        return attrs

    def create(self, validated_data):
        """Create prescription with items"""
        items_data = validated_data.pop('items')

        # Get doctor from context
        request = self.context.get('request')
        if request and request.user.type == 'doctor':
            validated_data['doctor'] = request.user

        # Create prescription
        prescription = Prescription.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)

        return prescription


class PrescriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating prescription (diagnosis and instructions only)
    """

    class Meta:
        model = Prescription
        fields = ['diagnosis', 'instructions']


# ======================== Statistics Serializers ========================

class MedicineStatsSerializer(serializers.Serializer):
    """
    Serializer for medicine statistics
    """
    total_medicines = serializers.IntegerField()
    by_form = serializers.DictField()
    most_prescribed = serializers.ListField()


class PrescriptionStatsSerializer(serializers.Serializer):
    """
    Serializer for prescription statistics
    """
    total_prescriptions = serializers.IntegerField()
    today_prescriptions = serializers.IntegerField()
    this_month_prescriptions = serializers.IntegerField()
    total_items = serializers.IntegerField()
    avg_items_per_prescription = serializers.FloatField()


class DoctorPrescriptionStatsSerializer(serializers.Serializer):
    """
    Serializer for doctor prescription statistics
    """
    doctor_id = serializers.IntegerField()
    doctor_name = serializers.CharField()
    total_prescriptions = serializers.IntegerField()
    total_items = serializers.IntegerField()