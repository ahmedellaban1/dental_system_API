"""
=============================================================================
medical/serializers.py - Medical Records & Diseases Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CommonDisease, ChronicDisease
from accounts.models import CustomUser
from etc.validators import validate_age


# ======================== Nested User Serializers ========================

class PatientMedicalSerializer(serializers.ModelSerializer):
    """
    Minimal patient info for medical records
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)
    date_of_birth = serializers.DateField(source='user_profile.date_of_birth', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone', 'date_of_birth']
        read_only_fields = fields


# ======================== Common Disease Serializers ========================

class CommonDiseaseListSerializer(serializers.ModelSerializer):
    """
    Minimal common disease serializer for lists
    """
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = CommonDisease
        fields = [
            'id', 'disease_name_ar', 'disease_name_en',
            'category', 'category_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CommonDiseaseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed common disease serializer
    """
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    patient_count = serializers.SerializerMethodField()

    class Meta:
        model = CommonDisease
        fields = [
            'id', 'disease_name_ar', 'disease_name_en',
            'description', 'category', 'category_display',
            'symptoms', 'common_treatments', 'patient_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_patient_count(self, obj):
        """Count how many patients have this disease"""
        return obj.patient_cases.filter(is_active=True).count()


class CommonDiseaseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating common diseases
    """

    class Meta:
        model = CommonDisease
        fields = [
            'disease_name_ar', 'disease_name_en', 'description',
            'category', 'symptoms', 'common_treatments'
        ]

    def validate_disease_name_ar(self, value):
        """Validate Arabic disease name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "اسم المرض بالعربي يجب أن يكون حرفين على الأقل / Arabic disease name must be at least 2 characters"
            )
        return value.strip()

    def validate_disease_name_en(self, value):
        """Validate English disease name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "اسم المرض بالإنجليزي يجب أن يكون حرفين على الأقل / English disease name must be at least 2 characters"
            )
        return value.strip()

    def validate(self, attrs):
        """Check for duplicates"""
        disease_name_ar = attrs.get('disease_name_ar')
        disease_name_en = attrs.get('disease_name_en')

        # Check if updating
        instance = self.instance

        # Check Arabic name duplicate
        if disease_name_ar:
            existing = CommonDisease.objects.filter(disease_name_ar__iexact=disease_name_ar)
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'disease_name_ar': 'مرض بهذا الاسم موجود بالفعل / Disease with this Arabic name already exists'
                })

        # Check English name duplicate
        if disease_name_en:
            existing = CommonDisease.objects.filter(disease_name_en__iexact=disease_name_en)
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'disease_name_en': 'مرض بهذا الاسم موجود بالفعل / Disease with this English name already exists'
                })

        return attrs


# ======================== Chronic Disease Serializers ========================

class ChronicDiseaseListSerializer(serializers.ModelSerializer):
    """
    Minimal chronic disease serializer for lists
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    disease_name_ar = serializers.CharField(source='disease.disease_name_ar', read_only=True)
    disease_name_en = serializers.CharField(source='disease.disease_name_en', read_only=True)
    disease_category = serializers.CharField(source='disease.get_category_display', read_only=True)

    class Meta:
        model = ChronicDisease
        fields = [
            'id', 'patient', 'patient_name', 'disease',
            'disease_name_ar', 'disease_name_en', 'disease_category',
            'diagnosed_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChronicDiseaseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed chronic disease serializer with nested relations
    """
    patient_details = PatientMedicalSerializer(source='patient', read_only=True)
    disease_details = CommonDiseaseDetailSerializer(source='disease', read_only=True)

    class Meta:
        model = ChronicDisease
        fields = [
            'id', 'patient', 'patient_details', 'disease', 'disease_details',
            'description', 'diagnosed_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChronicDiseaseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating chronic disease records
    """

    class Meta:
        model = ChronicDisease
        fields = [
            'patient', 'disease', 'description',
            'diagnosed_date', 'is_active'
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

    def validate_diagnosed_date(self, value):
        """Validate diagnosed date is not in the future"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "تاريخ التشخيص لا يمكن أن يكون في المستقبل / Diagnosed date cannot be in the future"
            )
        return value

    def validate(self, attrs):
        """Check for duplicate disease for patient"""
        patient = attrs.get('patient')
        disease = attrs.get('disease')

        # Check if updating
        instance = self.instance

        # Check if patient already has this disease
        if patient and disease:
            existing = ChronicDisease.objects.filter(
                patient=patient,
                disease=disease
            )
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'disease': f'المريض مسجل لديه هذا المرض بالفعل / Patient already has this disease recorded'
                })

        return attrs


class ChronicDiseaseUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating chronic disease records
    Cannot change patient or disease, only description and status
    """

    class Meta:
        model = ChronicDisease
        fields = ['description', 'diagnosed_date', 'is_active']

    def validate_diagnosed_date(self, value):
        """Validate diagnosed date is not in the future"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "تاريخ التشخيص لا يمكن أن يكون في المستقبل / Diagnosed date cannot be in the future"
            )
        return value


# ======================== Statistics Serializers ========================

class DiseaseCategoryStatsSerializer(serializers.Serializer):
    """
    Serializer for disease category statistics
    """
    category = serializers.CharField()
    category_display = serializers.CharField()
    disease_count = serializers.IntegerField()
    patient_count = serializers.IntegerField()


class PatientDiseaseStatsSerializer(serializers.Serializer):
    """
    Serializer for patient-specific disease statistics
    """
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    total_chronic_diseases = serializers.IntegerField()
    active_diseases = serializers.IntegerField()
    inactive_diseases = serializers.IntegerField()
    chronic_count = serializers.IntegerField()
    infectious_count = serializers.IntegerField()
    genetic_count = serializers.IntegerField()
    other_count = serializers.IntegerField()


class CommonDiseaseStatsSerializer(serializers.Serializer):
    """
    Serializer for common disease statistics
    """
    total_diseases = serializers.IntegerField()
    by_category = serializers.DictField()
    most_common = serializers.ListField()


class MedicalOverviewSerializer(serializers.Serializer):
    """
    Serializer for medical system overview
    """
    total_patients_with_chronic = serializers.IntegerField()
    total_chronic_disease_records = serializers.IntegerField()
    total_active_diseases = serializers.IntegerField()
    total_disease_library = serializers.IntegerField()
    category_breakdown = serializers.DictField()