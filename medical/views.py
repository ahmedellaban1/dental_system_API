"""
=============================================================================
medical/views.py - Medical Records & Diseases Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q
from collections import defaultdict

from .models import CommonDisease, ChronicDisease
from .serializers import (
    CommonDiseaseListSerializer, CommonDiseaseDetailSerializer,
    CommonDiseaseCreateSerializer, ChronicDiseaseListSerializer,
    ChronicDiseaseDetailSerializer, ChronicDiseaseCreateSerializer,
    ChronicDiseaseUpdateSerializer, DiseaseCategoryStatsSerializer,
    PatientDiseaseStatsSerializer, CommonDiseaseStatsSerializer,
    MedicalOverviewSerializer
)
from etc.permissions import (
    CanManageCommonDiseases, CanViewMedicalRecord,
    CanManageMedicalRecord, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class CommonDiseaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing common diseases library
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin and Doctors
    """
    queryset = CommonDisease.objects.all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['disease_name_ar', 'disease_name_en', 'description', 'symptoms']
    ordering_fields = ['disease_name_ar', 'disease_name_en', 'category', 'created_at']
    ordering = ['disease_name_ar']
    permission_classes = [CanManageCommonDiseases]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommonDiseaseCreateSerializer
        elif self.action == 'list':
            return CommonDiseaseListSerializer
        return CommonDiseaseDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب الأمراض بنجاح / Diseases retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل المرض بنجاح / Disease details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            disease = serializer.save()
            return created(
                message="تم إضافة المرض بنجاح / Disease added successfully",
                data=CommonDiseaseDetailSerializer(disease).data
            )

        return bad_request(
            message="فشل إضافة المرض / Failed to add disease",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            disease = serializer.save()
            return success(
                message="تم تحديث المرض بنجاح / Disease updated successfully",
                data=CommonDiseaseDetailSerializer(disease).data
            )

        return bad_request(
            message="فشل تحديث المرض / Failed to update disease",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            disease = serializer.save()
            return success(
                message="تم تحديث المرض بنجاح / Disease updated successfully",
                data=CommonDiseaseDetailSerializer(disease).data
            )

        return bad_request(
            message="فشل تحديث المرض / Failed to update disease",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if disease is used by any patient
        if instance.patient_cases.exists():
            return bad_request(
                message="لا يمكن حذف هذا المرض لأنه مسجل لدى مرضى / Cannot delete disease as it is assigned to patients"
            )

        instance.delete()
        return success(
            message="تم حذف المرض بنجاح / Disease deleted successfully"
        )

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get diseases grouped by category"""
        category = request.query_params.get('category')

        if category:
            queryset = self.queryset.filter(category=category)
        else:
            queryset = self.queryset

        queryset = self.filter_queryset(queryset)
        serializer = CommonDiseaseListSerializer(queryset, many=True)

        return success(
            message="الأمراض حسب الفئة / Diseases by category",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get disease library statistics (staff only)"""
        from etc.choices import CATEGORY_CHOICES

        total = self.queryset.count()

        # Count by category
        by_category = {}
        for cat_code, cat_name in CATEGORY_CHOICES:
            count = self.queryset.filter(category=cat_code).count()
            by_category[cat_name] = count

        # Most common diseases (by patient count)
        most_common = self.queryset.annotate(
            patient_count=Count('patient_cases', filter=Q(patient_cases__is_active=True))
        ).order_by('-patient_count')[:10]

        most_common_list = [
            {
                'id': d.id,
                'name_ar': d.disease_name_ar,
                'name_en': d.disease_name_en,
                'patient_count': d.patient_count
            }
            for d in most_common
        ]

        stats = {
            'total_diseases': total,
            'by_category': by_category,
            'most_common': most_common_list
        }

        serializer = CommonDiseaseStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات مكتبة الأمراض / Disease library statistics",
            data=serializer.data
        )

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        """Get list of patients with this disease"""
        disease = self.get_object()
        chronic_diseases = ChronicDisease.objects.filter(
            disease=disease,
            is_active=True
        ).select_related('patient', 'patient__user_profile')

        serializer = ChronicDiseaseListSerializer(chronic_diseases, many=True)

        return success(
            message=f"المرضى المصابون بـ {disease.disease_name_ar} / Patients with {disease.disease_name_en}",
            data=serializer.data
        )


class ChronicDiseaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient chronic diseases
    - List/Retrieve: Staff/Doctors see all, Patients see own
    - Create/Update: Doctors and Staff
    - Delete: Admin only
    """
    queryset = ChronicDisease.objects.select_related(
        'patient', 'disease', 'patient__user_profile'
    ).all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'disease', 'disease__category', 'is_active']
    search_fields = ['patient__first_name', 'patient__last_name', 'disease__disease_name_ar',
                     'disease__disease_name_en']
    ordering_fields = ['diagnosed_date', 'created_at']
    ordering = ['-diagnosed_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return ChronicDiseaseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ChronicDiseaseUpdateSerializer
        elif self.action == 'list':
            return ChronicDiseaseListSerializer
        return ChronicDiseaseDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [CanManageMedicalRecord()]
        elif self.action == 'destroy':
            return [IsStaff()]
        return [CanViewMedicalRecord()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Staff and doctors can see all records
        if user.type in ['admin', 'receptionist', 'doctor']:
            return self.queryset

        # Patients can see their own records
        if user.type == 'patient':
            return self.queryset.filter(patient=user)

        return self.queryset.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب السجلات الطبية بنجاح / Medical records retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل السجل الطبي بنجاح / Medical record details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            record = serializer.save()
            return created(
                message="تم إضافة السجل الطبي بنجاح / Medical record added successfully",
                data=ChronicDiseaseDetailSerializer(record).data
            )

        return bad_request(
            message="فشل إضافة السجل الطبي / Failed to add medical record",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            record = serializer.save()
            return success(
                message="تم تحديث السجل الطبي بنجاح / Medical record updated successfully",
                data=ChronicDiseaseDetailSerializer(record).data
            )

        return bad_request(
            message="فشل تحديث السجل الطبي / Failed to update medical record",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            record = serializer.save()
            return success(
                message="تم تحديث السجل الطبي بنجاح / Medical record updated successfully",
                data=ChronicDiseaseDetailSerializer(record).data
            )

        return bad_request(
            message="فشل تحديث السجل الطبي / Failed to update medical record",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف السجل الطبي بنجاح / Medical record deleted successfully"
        )

    @action(detail=False, methods=['get'])
    def my_diseases(self, request):
        """Get current patient's chronic diseases"""
        if request.user.type != 'patient':
            return forbidden(
                message="هذا الإجراء متاح للمرضى فقط / This action is only available for patients"
            )

        queryset = self.get_queryset().filter(patient=request.user)
        queryset = self.filter_queryset(queryset)
        serializer = ChronicDiseaseListSerializer(queryset, many=True)

        return success(
            message="سجلاتك الطبية / Your medical records",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active chronic diseases"""
        queryset = self.get_queryset().filter(is_active=True)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ChronicDiseaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ChronicDiseaseListSerializer(queryset, many=True)
        return success(
            message="الأمراض المزمنة النشطة / Active chronic diseases",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def inactive(self, request):
        """Get inactive chronic diseases"""
        queryset = self.get_queryset().filter(is_active=False)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ChronicDiseaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ChronicDiseaseListSerializer(queryset, many=True)
        return success(
            message="الأمراض المزمنة غير النشطة / Inactive chronic diseases",
            data=serializer.data
        )

    @action(detail=True, methods=['post'], permission_classes=[CanManageMedicalRecord])
    def deactivate(self, request, pk=None):
        """Mark chronic disease as inactive (recovered/controlled)"""
        record = self.get_object()

        if not record.is_active:
            return bad_request(
                message="السجل غير نشط بالفعل / Record is already inactive"
            )

        record.is_active = False
        record.save()

        return success(
            message="تم تعطيل السجل بنجاح / Record deactivated successfully",
            data=ChronicDiseaseDetailSerializer(record).data
        )

    @action(detail=True, methods=['post'], permission_classes=[CanManageMedicalRecord])
    def activate(self, request, pk=None):
        """Mark chronic disease as active again"""
        record = self.get_object()

        if record.is_active:
            return bad_request(
                message="السجل نشط بالفعل / Record is already active"
            )

        record.is_active = True
        record.save()

        return success(
            message="تم تفعيل السجل بنجاح / Record activated successfully",
            data=ChronicDiseaseDetailSerializer(record).data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_patient(self, request):
        """Get chronic diseases for a specific patient (staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب / Patient ID is required"
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        serializer = ChronicDiseaseListSerializer(queryset, many=True)

        return success(
            message="السجلات الطبية للمريض / Patient's medical records",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def patient_summary(self, request):
        """Get medical summary for a specific patient (staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب / Patient ID is required"
            )

        from accounts.models import CustomUser
        try:
            patient = CustomUser.objects.get(id=patient_id, type='patient')
        except CustomUser.DoesNotExist:
            return not_found(
                message="المريض غير موجود / Patient not found"
            )

        diseases = self.queryset.filter(patient_id=patient_id)

        # Count by category
        from etc.choices import CATEGORY_CHOICES
        category_counts = {}
        for cat_code, cat_name in CATEGORY_CHOICES:
            count = diseases.filter(disease__category=cat_code, is_active=True).count()
            category_counts[cat_code + '_count'] = count

        summary = {
            'patient_id': patient.id,
            'patient_name': patient.get_full_name(),
            'total_chronic_diseases': diseases.count(),
            'active_diseases': diseases.filter(is_active=True).count(),
            'inactive_diseases': diseases.filter(is_active=False).count(),
            **category_counts
        }

        serializer = PatientDiseaseStatsSerializer(data=summary)
        serializer.is_valid()

        return success(
            message=f"ملخص طبي لـ {patient.get_full_name()} / Medical summary for {patient.get_full_name()}",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def overview(self, request):
        """Get medical system overview (staff only)"""
        from etc.choices import CATEGORY_CHOICES

        all_records = self.queryset

        # Count unique patients with chronic diseases
        patients_with_chronic = all_records.values('patient').distinct().count()

        # Category breakdown
        category_breakdown = {}
        for cat_code, cat_name in CATEGORY_CHOICES:
            count = all_records.filter(disease__category=cat_code, is_active=True).count()
            category_breakdown[cat_name] = count

        overview = {
            'total_patients_with_chronic': patients_with_chronic,
            'total_chronic_disease_records': all_records.count(),
            'total_active_diseases': all_records.filter(is_active=True).count(),
            'total_disease_library': CommonDisease.objects.count(),
            'category_breakdown': category_breakdown
        }

        serializer = MedicalOverviewSerializer(data=overview)
        serializer.is_valid()

        return success(
            message="نظرة عامة على النظام الطبي / Medical system overview",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def category_statistics(self, request):
        """Get statistics by disease category (staff only)"""
        from etc.choices import CATEGORY_CHOICES

        stats = []
        for cat_code, cat_name in CATEGORY_CHOICES:
            disease_count = CommonDisease.objects.filter(category=cat_code).count()
            patient_count = self.queryset.filter(
                disease__category=cat_code,
                is_active=True
            ).values('patient').distinct().count()

            stats.append({
                'category': cat_code,
                'category_display': cat_name,
                'disease_count': disease_count,
                'patient_count': patient_count
            })

        serializer = DiseaseCategoryStatsSerializer(data=stats, many=True)
        serializer.is_valid()

        return success(
            message="إحصائيات حسب فئة المرض / Statistics by disease category",
            data=serializer.data
        )