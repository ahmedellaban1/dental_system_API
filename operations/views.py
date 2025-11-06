"""
=============================================================================
operations/views.py - Operations & Media Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta

from .models import Operation, OperationMedia
from .serializers import (
    OperationListSerializer, OperationDetailSerializer,
    OperationCreateSerializer, OperationUpdateSerializer,
    OperationStatusUpdateSerializer, OperationMediaListSerializer,
    OperationMediaDetailSerializer, OperationMediaCreateSerializer,
    OperationStatsSerializer, DoctorOperationStatsSerializer,
    OperationTypeStatsSerializer
)
from etc.permissions import (
    CanViewOperation, CanManageOperation,
    CanManageOperationMedia, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class OperationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dental operations
    - List: Role-based (patients see own, doctors see own, staff see all)
    - Create: Doctors and Admin
    - Update: Doctors (own) and Admin
    - Delete: Admin only
    """
    queryset = Operation.objects.select_related(
        'patient', 'doctor', 'booking',
        'patient__user_profile', 'doctor__user_profile'
    ).prefetch_related('media_files').all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'doctor', 'patient', 'operation_date']
    search_fields = ['operation_name', 'patient__first_name', 'patient__last_name', 'description']
    ordering_fields = ['operation_date', 'cost', 'created_at', 'status']
    ordering = ['-operation_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return OperationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OperationUpdateSerializer
        elif self.action == 'list':
            return OperationListSerializer
        return OperationDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [CanManageOperation()]
        elif self.action == 'destroy':
            return [IsStaff()]
        return [CanViewOperation()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Staff can see all operations
        if user.type in ['admin', 'receptionist']:
            return self.queryset

        # Doctors can see their operations
        if user.type == 'doctor':
            return self.queryset.filter(doctor=user)

        # Patients can see their operations
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
            message="تم جلب العمليات بنجاح / Operations retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل العملية بنجاح / Operation details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            operation = serializer.save()
            return created(
                message="تم إنشاء العملية بنجاح / Operation created successfully",
                data=OperationDetailSerializer(operation, context={'request': request}).data
            )

        return bad_request(
            message="فشل إنشاء العملية / Failed to create operation",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            operation = serializer.save()
            return success(
                message="تم تحديث العملية بنجاح / Operation updated successfully",
                data=OperationDetailSerializer(operation, context={'request': request}).data
            )

        return bad_request(
            message="فشل تحديث العملية / Failed to update operation",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            operation = serializer.save()
            return success(
                message="تم تحديث العملية بنجاح / Operation updated successfully",
                data=OperationDetailSerializer(operation, context={'request': request}).data
            )

        return bad_request(
            message="فشل تحديث العملية / Failed to update operation",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if operation has bills
        if hasattr(instance, 'bills') and instance.bills.exists():
            return bad_request(
                message="لا يمكن حذف عملية لها فواتير / Cannot delete operation with bills"
            )

        instance.delete()
        return success(
            message="تم حذف العملية بنجاح / Operation deleted successfully"
        )

    # ======================== Status Management ========================

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update operation status"""
        operation = self.get_object()
        serializer = OperationStatusUpdateSerializer(data=request.data)

        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')

            # Validate status transition
            if operation.status == 'completed' and new_status != 'completed':
                return bad_request(
                    message="لا يمكن تغيير حالة عملية مكتملة / Cannot change status of completed operation"
                )

            if operation.status == 'cancelled' and new_status != 'cancelled':
                return bad_request(
                    message="لا يمكن تغيير حالة عملية ملغية / Cannot change status of cancelled operation"
                )

            operation.status = new_status
            if notes:
                operation.notes = f"{operation.notes}\n{notes}" if operation.notes else notes
            operation.save()

            return success(
                message="تم تحديث حالة العملية بنجاح / Operation status updated successfully",
                data=OperationDetailSerializer(operation, context={'request': request}).data
            )

        return bad_request(
            message="فشل تحديث الحالة / Failed to update status",
            errors=serializer.errors
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark operation as completed"""
        operation = self.get_object()

        if operation.status == 'completed':
            return bad_request(
                message="العملية مكتملة بالفعل / Operation is already completed"
            )

        if operation.status == 'cancelled':
            return bad_request(
                message="لا يمكن إكمال عملية ملغية / Cannot complete cancelled operation"
            )

        operation.status = 'completed'
        operation.save()

        return success(
            message="تم تحديث حالة العملية إلى مكتمل / Operation marked as completed",
            data=OperationDetailSerializer(operation, context={'request': request}).data
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel operation"""
        operation = self.get_object()

        if operation.status == 'cancelled':
            return bad_request(
                message="العملية ملغية بالفعل / Operation is already cancelled"
            )

        if operation.status == 'completed':
            return bad_request(
                message="لا يمكن إلغاء عملية مكتملة / Cannot cancel completed operation"
            )

        operation.status = 'cancelled'
        operation.save()

        return success(
            message="تم إلغاء العملية بنجاح / Operation cancelled successfully",
            data=OperationDetailSerializer(operation, context={'request': request}).data
        )

    # ======================== Filtering Actions ========================

    @action(detail=False, methods=['get'])
    def my_operations(self, request):
        """Get current user's operations (patient or doctor)"""
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
            serializer = OperationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OperationListSerializer(queryset, many=True)
        return success(
            message="عملياتك / Your operations",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def scheduled(self, request):
        """Get scheduled operations"""
        queryset = self.get_queryset().filter(status='scheduled')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = OperationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OperationListSerializer(queryset, many=True)
        return success(
            message="العمليات المجدولة / Scheduled operations",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed operations"""
        queryset = self.get_queryset().filter(status='completed')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = OperationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OperationListSerializer(queryset, many=True)
        return success(
            message="العمليات المكتملة / Completed operations",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's operations"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(operation_date=today)
        serializer = OperationListSerializer(queryset, many=True)

        return success(
            message=f"عمليات اليوم ({today}) / Today's operations ({today})",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_doctor(self, request):
        """Get operations by doctor (staff only)"""
        doctor_id = request.query_params.get('doctor')

        if not doctor_id:
            return bad_request(
                message="معرف الطبيب مطلوب / Doctor ID is required"
            )

        queryset = self.queryset.filter(doctor_id=doctor_id)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = OperationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OperationListSerializer(queryset, many=True)
        return success(
            message="عمليات الطبيب / Doctor's operations",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_patient(self, request):
        """Get operations by patient (staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب / Patient ID is required"
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        queryset = self.filter_queryset(queryset)
        serializer = OperationListSerializer(queryset, many=True)

        return success(
            message="عمليات المريض / Patient's operations",
            data=serializer.data
        )

    # ======================== Statistics Actions ========================

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get operation statistics (staff only)"""
        all_operations = self.queryset
        today = timezone.now().date()
        first_day_month = today.replace(day=1)

        # Count by status
        status_counts = all_operations.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Calculate revenue
        total_revenue = all_operations.filter(
            status='completed'
        ).aggregate(total=Sum('cost'))['total'] or 0

        stats = {
            'total_operations': all_operations.count(),
            'scheduled_operations': status_dict.get('scheduled', 0),
            'in_progress_operations': status_dict.get('in_progress', 0),
            'completed_operations': status_dict.get('completed', 0),
            'cancelled_operations': status_dict.get('cancelled', 0),
            'total_revenue': total_revenue,
            'today_operations': all_operations.filter(operation_date=today).count(),
            'this_month_operations': all_operations.filter(operation_date__gte=first_day_month).count(),
        }

        serializer = OperationStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات العمليات / Operation statistics",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def doctor_statistics(self, request):
        """Get statistics grouped by doctor (staff only)"""
        from accounts.models import CustomUser

        doctors = CustomUser.objects.filter(type='doctor', is_active=True)
        stats = []

        for doctor in doctors:
            operations = self.queryset.filter(doctor=doctor)
            completed = operations.filter(status='completed')
            revenue = completed.aggregate(total=Sum('cost'))['total'] or 0

            stats.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.get_full_name(),
                'total_operations': operations.count(),
                'completed_operations': completed.count(),
                'total_revenue': revenue
            })

        serializer = DoctorOperationStatsSerializer(data=stats, many=True)
        serializer.is_valid()

        return success(
            message="إحصائيات الأطباء / Doctor statistics",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def operation_types(self, request):
        """Get statistics by operation type (staff only)"""
        stats = self.queryset.values('operation_name').annotate(
            count=Count('id'),
            total_revenue=Sum('cost', filter=Q(status='completed')),
            avg_cost=Avg('cost')
        ).order_by('-count')[:20]

        serializer = OperationTypeStatsSerializer(data=stats, many=True)
        serializer.is_valid()

        return success(
            message="إحصائيات أنواع العمليات / Operation type statistics",
            data=serializer.data
        )


class OperationMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing operation media files
    - Upload: Doctors (own operations) and Admin
    - View: Same as operation permissions
    - Delete: Doctors (own) and Admin
    """
    queryset = OperationMedia.objects.select_related('operation', 'operation__patient', 'operation__doctor').all()
    pagination_class = DefaultPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['operation', 'media_type']
    search_fields = ['description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OperationMediaCreateSerializer
        elif self.action == 'list':
            return OperationMediaListSerializer
        return OperationMediaDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [CanManageOperationMedia()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role and operation access"""
        user = self.request.user

        # Staff can see all media
        if user.type in ['admin', 'receptionist']:
            return self.queryset

        # Doctors can see media from their operations
        if user.type == 'doctor':
            return self.queryset.filter(operation__doctor=user)

        # Patients can see media from their operations
        if user.type == 'patient':
            return self.queryset.filter(operation__patient=user)

        return self.queryset.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return success(
            message="تم جلب ملفات الوسائط بنجاح / Media files retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return success(
            message="تم جلب تفاصيل الملف بنجاح / Media file details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            media = serializer.save()
            return created(
                message="تم رفع الملف بنجاح / File uploaded successfully",
                data=OperationMediaDetailSerializer(media, context={'request': request}).data
            )

        return bad_request(
            message="فشل رفع الملف / Failed to upload file",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Delete file from storage
        if instance.file_path:
            instance.file_path.delete(save=False)

        instance.delete()
        return success(
            message="تم حذف الملف بنجاح / File deleted successfully"
        )

    @action(detail=False, methods=['get'])
    def by_operation(self, request):
        """Get media files for a specific operation"""
        operation_id = request.query_params.get('operation')

        if not operation_id:
            return bad_request(
                message="معرف العملية مطلوب / Operation ID is required"
            )

        queryset = self.get_queryset().filter(operation_id=operation_id)
        serializer = OperationMediaListSerializer(queryset, many=True, context={'request': request})

        return success(
            message="ملفات العملية / Operation media files",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get media files by type"""
        media_type = request.query_params.get('type')

        if not media_type:
            return bad_request(
                message="نوع الوسائط مطلوب / Media type is required"
            )

        queryset = self.get_queryset().filter(media_type=media_type)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = OperationMediaListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = OperationMediaListSerializer(queryset, many=True, context={'request': request})
        return success(
            message=f"ملفات من نوع {media_type} / Media files of type {media_type}",
            data=serializer.data
        )