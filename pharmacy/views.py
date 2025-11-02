"""
=============================================================================
pharmacy/views.py - Pharmacy & Prescription Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import date

from .models import MedicineLibrary, Prescription, PrescriptionItem
from .serializers import (
    MedicineListSerializer, MedicineDetailSerializer,
    MedicineCreateSerializer, PrescriptionListSerializer,
    PrescriptionDetailSerializer, PrescriptionCreateSerializer,
    PrescriptionUpdateSerializer, MedicineStatsSerializer,
    PrescriptionStatsSerializer, DoctorPrescriptionStatsSerializer
)
from etc.permissions import (
    CanManageMedicineLibrary, CanViewPrescription,
    CanManagePrescription, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class MedicineLibraryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medicine library
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin and Doctors
    """
    queryset = MedicineLibrary.objects.all()
    pagination_class = DefaultPagination
    permission_classes = [CanManageMedicineLibrary]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['form']
    search_fields = ['trade_name', 'active_ingredient', 'description']
    ordering_fields = ['trade_name', 'times_prescribed', 'created_at']
    ordering = ['trade_name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MedicineCreateSerializer
        elif self.action == 'list':
            return MedicineListSerializer
        return MedicineDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب الأدوية بنجاح / Medicines retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل الدواء بنجاح / Medicine details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            medicine = serializer.save()
            return created(
                message="تم إضافة الدواء بنجاح / Medicine added successfully",
                data=MedicineDetailSerializer(medicine).data
            )

        return bad_request(
            message="فشل إضافة الدواء / Failed to add medicine",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            medicine = serializer.save()
            return success(
                message="تم تحديث الدواء بنجاح / Medicine updated successfully",
                data=MedicineDetailSerializer(medicine).data
            )

        return bad_request(
            message="فشل تحديث الدواء / Failed to update medicine",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            medicine = serializer.save()
            return success(
                message="تم تحديث الدواء بنجاح / Medicine updated successfully",
                data=MedicineDetailSerializer(medicine).data
            )

        return bad_request(
            message="فشل تحديث الدواء / Failed to update medicine",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if medicine is used in any prescription
        if instance.prescription_items.exists():
            return bad_request(
                message="لا يمكن حذف دواء مستخدم في روشتات / Cannot delete medicine used in prescriptions"
            )

        instance.delete()
        return success(
            message="تم حذف الدواء بنجاح / Medicine deleted successfully"
        )

    @action(detail=False, methods=['get'])
    def by_form(self, request):
        """Get medicines by form"""
        form = request.query_params.get('form')

        if form:
            queryset = self.queryset.filter(form=form)
        else:
            queryset = self.queryset

        queryset = self.filter_queryset(queryset)
        serializer = MedicineListSerializer(queryset, many=True)

        return success(
            message="الأدوية حسب الشكل الدوائي / Medicines by form",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def most_prescribed(self, request):
        """Get most prescribed medicines"""
        limit = int(request.query_params.get('limit', 20))

        queryset = self.queryset.order_by('-times_prescribed')[:limit]
        serializer = MedicineListSerializer(queryset, many=True)

        return success(
            message="الأدوية الأكثر وصفاً / Most prescribed medicines",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get medicine library statistics (staff only)"""
        from etc.choices import FORM_CHOICES

        total = self.queryset.count()

        # Count by form
        by_form = {}
        for form_code, form_name in FORM_CHOICES:
            count = self.queryset.filter(form=form_code).count()
            by_form[form_name] = count

        # Most prescribed
        most_prescribed = self.queryset.order_by('-times_prescribed')[:10]
        most_prescribed_list = [
            {
                'id': m.id,
                'trade_name': m.trade_name,
                'active_ingredient': m.active_ingredient,
                'times_prescribed': m.times_prescribed
            }
            for m in most_prescribed
        ]

        stats = {
            'total_medicines': total,
            'by_form': by_form,
            'most_prescribed': most_prescribed_list
        }

        serializer = MedicineStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات مكتبة الأدوية / Medicine library statistics",
            data=serializer.data
        )


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prescriptions
    - List: Role-based (patients see own, doctors see own, staff see all)
    - Create: Doctors only
    - Update: Doctors (own only)
    - Delete: Admin only
    """
    queryset = Prescription.objects.select_related(
        'patient', 'doctor', 'booking',
        'patient__user_profile', 'doctor__user_profile'
    ).prefetch_related('items', 'items__medicine').all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'prescription_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'diagnosis']
    ordering_fields = ['prescription_date', 'created_at']
    ordering = ['-prescription_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PrescriptionUpdateSerializer
        elif self.action == 'list':
            return PrescriptionListSerializer
        return PrescriptionDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [CanManagePrescription()]
        elif self.action in ['update', 'partial_update']:
            return [CanManagePrescription()]
        elif self.action == 'destroy':
            return [IsStaff()]
        return [CanViewPrescription()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Staff can see all prescriptions
        if user.type in ['admin', 'receptionist']:
            return self.queryset

        # Doctors can see their prescriptions
        if user.type == 'doctor':
            return self.queryset.filter(doctor=user)

        # Patients can see their prescriptions
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
            message="تم جلب الروشتات بنجاح / Prescriptions retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل الروشتة بنجاح / Prescription details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            prescription = serializer.save()
            return created(
                message="تم إنشاء الروشتة بنجاح / Prescription created successfully",
                data=PrescriptionDetailSerializer(prescription).data
            )

        return bad_request(
            message="فشل إنشاء الروشتة / Failed to create prescription",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            prescription = serializer.save()
            return success(
                message="تم تحديث الروشتة بنجاح / Prescription updated successfully",
                data=PrescriptionDetailSerializer(prescription).data
            )

        return bad_request(
            message="فشل تحديث الروشتة / Failed to update prescription",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            prescription = serializer.save()
            return success(
                message="تم تحديث الروشتة بنجاح / Prescription updated successfully",
                data=PrescriptionDetailSerializer(prescription).data
            )

        return bad_request(
            message="فشل تحديث الروشتة / Failed to update prescription",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف الروشتة بنجاح / Prescription deleted successfully"
        )

    @action(detail=False, methods=['get'])
    def my_prescriptions(self, request):
        """Get current user's prescriptions (patient or doctor)"""
        user = request.user

        if user.type == 'patient':
            queryset = self.get_queryset().filter(patient=user)
        elif user.type == 'doctor':
            queryset = self.get_queryset().filter(doctor=user)
        else:
            queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PrescriptionListSerializer(queryset, many=True)
        return success(
            message="روشتاتك / Your prescriptions",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's prescriptions"""
        today = date.today()
        queryset = self.get_queryset().filter(prescription_date=today)
        serializer = PrescriptionListSerializer(queryset, many=True)

        return success(
            message=f"روشتات اليوم ({today}) / Today's prescriptions ({today})",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_doctor(self, request):
        """Get prescriptions by doctor (staff only)"""
        doctor_id = request.query_params.get('doctor')

        if not doctor_id:
            return bad_request(
                message="معرف الطبيب مطلوب / Doctor ID is required"
            )

        queryset = self.queryset.filter(doctor_id=doctor_id)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PrescriptionListSerializer(queryset, many=True)
        return success(
            message="روشتات الطبيب / Doctor's prescriptions",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_patient(self, request):
        """Get prescriptions by patient (staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب / Patient ID is required"
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        queryset = self.filter_queryset(queryset)
        serializer = PrescriptionListSerializer(queryset, many=True)

        return success(
            message="روشتات المريض / Patient's prescriptions",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get prescription statistics (staff only)"""
        all_prescriptions = self.queryset
        today = date.today()
        first_day_month = date(today.year, today.month, 1)

        # Count items
        total_items = PrescriptionItem.objects.count()
        avg_items = all_prescriptions.annotate(
            item_count=Count('items')
        ).aggregate(avg=Avg('item_count'))['avg'] or 0

        stats = {
            'total_prescriptions': all_prescriptions.count(),
            'today_prescriptions': all_prescriptions.filter(prescription_date=today).count(),
            'this_month_prescriptions': all_prescriptions.filter(prescription_date__gte=first_day_month).count(),
            'total_items': total_items,
            'avg_items_per_prescription': round(avg_items, 2)
        }

        serializer = PrescriptionStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات الروشتات / Prescription statistics",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def doctor_statistics(self, request):
        """Get statistics grouped by doctor (staff only)"""
        from accounts.models import CustomUser

        doctors = CustomUser.objects.filter(type='doctor', is_active=True)
        stats = []

        for doctor in doctors:
            prescriptions = self.queryset.filter(doctor=doctor)
            total_items = PrescriptionItem.objects.filter(
                prescription__doctor=doctor
            ).count()

            stats.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.get_full_name(),
                'total_prescriptions': prescriptions.count(),
                'total_items': total_items
            })

        serializer = DoctorPrescriptionStatsSerializer(data=stats, many=True)
        serializer.is_valid()

        return success(
            message="إحصائيات الأطباء / Doctor statistics",
            data=serializer.data
        )