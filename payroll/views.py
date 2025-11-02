"""
=============================================================================
payroll/views.py - Payroll & Salary Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import date

from .models import Salary, Advance
from .serializers import (
    SalaryListSerializer, SalaryDetailSerializer,
    SalaryCreateSerializer, SalaryUpdateSerializer,
    SalaryPaymentSerializer, AdvanceListSerializer,
    AdvanceDetailSerializer, AdvanceRequestSerializer,
    AdvanceApprovalSerializer, SalaryStatsSerializer,
    AdvanceStatsSerializer, ReceptionistPayrollSummarySerializer
)
from etc.permissions import (
    CanManageSalary, CanViewAdvance, CanRequestAdvance,
    CanApproveAdvance, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class SalaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing receptionist salaries
    - List: Admin see all, Receptionists see own
    - Create/Update/Delete: Admin only
    """
    queryset = Salary.objects.select_related(
        'receptionist', 'receptionist__user_profile'
    ).all()
    pagination_class = DefaultPagination
    permission_classes = [CanManageSalary]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'receptionist', 'salary_month']
    search_fields = ['receptionist__first_name', 'receptionist__last_name', 'notes']
    ordering_fields = ['salary_month', 'net_salary', 'created_at']
    ordering = ['-salary_month']

    def get_serializer_class(self):
        if self.action == 'create':
            return SalaryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SalaryUpdateSerializer
        elif self.action == 'list':
            return SalaryListSerializer
        return SalaryDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Admin can see all salaries
        if user.type == 'admin':
            return self.queryset

        # Receptionists can see their own salaries
        if user.type == 'receptionist':
            return self.queryset.filter(receptionist=user)

        return self.queryset.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب الرواتب بنجاح / Salaries retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل الراتب بنجاح / Salary details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            salary = serializer.save()
            return created(
                message="تم إنشاء سجل الراتب بنجاح / Salary record created successfully",
                data=SalaryDetailSerializer(salary).data
            )

        return bad_request(
            message="فشل إنشاء سجل الراتب / Failed to create salary record",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            salary = serializer.save()
            return success(
                message="تم تحديث الراتب بنجاح / Salary updated successfully",
                data=SalaryDetailSerializer(salary).data
            )

        return bad_request(
            message="فشل تحديث الراتب / Failed to update salary",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            salary = serializer.save()
            return success(
                message="تم تحديث الراتب بنجاح / Salary updated successfully",
                data=SalaryDetailSerializer(salary).data
            )

        return bad_request(
            message="فشل تحديث الراتب / Failed to update salary",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف سجل الراتب بنجاح / Salary record deleted successfully"
        )

    # ======================== Payment Actions ========================

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def mark_paid(self, request, pk=None):
        """Mark salary as paid (admin only)"""
        salary = self.get_object()

        if salary.status == 'paid':
            return bad_request(
                message="الراتب مدفوع بالفعل / Salary is already paid"
            )

        serializer = SalaryPaymentSerializer(data=request.data)
        if serializer.is_valid():
            salary.status = 'paid'
            salary.payment_date = serializer.validated_data.get('payment_date', date.today())

            notes = serializer.validated_data.get('notes', '')
            if notes:
                salary.notes = f"{salary.notes}\n{notes}" if salary.notes else notes

            salary.save()

            return success(
                message="تم تحديث حالة الراتب إلى مدفوع / Salary marked as paid",
                data=SalaryDetailSerializer(salary).data
            )

        return bad_request(errors=serializer.errors)

    # ======================== Filtering Actions ========================

    @action(detail=False, methods=['get'])
    def my_salaries(self, request):
        """Get current receptionist's salaries"""
        if request.user.type != 'receptionist':
            return forbidden(
                message="هذا الإجراء متاح لموظفي الاستقبال فقط / This action is only available for receptionists"
            )

        queryset = self.get_queryset().filter(receptionist=request.user)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SalaryListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SalaryListSerializer(queryset, many=True)
        return success(
            message="رواتبك / Your salaries",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending salaries"""
        queryset = self.get_queryset().filter(status='pending')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SalaryListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SalaryListSerializer(queryset, many=True)
        return success(
            message="الرواتب المعلقة / Pending salaries",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def this_month(self, request):
        """Get this month's salaries"""
        today = date.today()
        first_day = date(today.year, today.month, 1)

        queryset = self.get_queryset().filter(salary_month=first_day)
        serializer = SalaryListSerializer(queryset, many=True)

        return success(
            message=f"رواتب شهر {first_day.strftime('%B %Y')} / Salaries for {first_day.strftime('%B %Y')}",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_receptionist(self, request):
        """Get salaries by receptionist (admin only)"""
        receptionist_id = request.query_params.get('receptionist')

        if not receptionist_id:
            return bad_request(
                message="معرف موظف الاستقبال مطلوب / Receptionist ID is required"
            )

        queryset = self.queryset.filter(receptionist_id=receptionist_id)
        queryset = self.filter_queryset(queryset)
        serializer = SalaryListSerializer(queryset, many=True)

        return success(
            message="رواتب موظف الاستقبال / Receptionist's salaries",
            data=serializer.data
        )

    # ======================== Statistics Actions ========================

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get salary statistics (admin only)"""
        all_salaries = self.queryset
        today = date.today()
        first_day_month = date(today.year, today.month, 1)

        # Count by status
        status_counts = all_salaries.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Calculate totals
        totals = all_salaries.aggregate(
            total_amount=Sum('net_salary'),
            total_paid=Sum('net_salary', filter=Q(status='paid')),
            total_pending=Sum('net_salary', filter=Q(status='pending'))
        )

        this_month_total = all_salaries.filter(
            salary_month=first_day_month
        ).aggregate(total=Sum('net_salary'))['total'] or 0

        stats = {
            'total_salaries': all_salaries.count(),
            'pending_salaries': status_dict.get('pending', 0),
            'partial_salaries': status_dict.get('partial', 0),
            'paid_salaries': status_dict.get('paid', 0),
            'total_amount': totals['total_amount'] or 0,
            'total_paid': totals['total_paid'] or 0,
            'total_pending': totals['total_pending'] or 0,
            'this_month_total': this_month_total,
        }

        serializer = SalaryStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات الرواتب / Salary statistics",
            data=serializer.data
        )


class AdvanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing salary advances
    - List: Admin see all, Receptionists see own
    - Request: Receptionists only
    - Approve/Reject: Admin only
    """
    queryset = Advance.objects.select_related(
        'receptionist', 'approved_by',
        'receptionist__user_profile'
    ).all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'receptionist']
    search_fields = ['receptionist__first_name', 'receptionist__last_name', 'reason']
    ordering_fields = ['request_date', 'amount', 'status']
    ordering = ['-request_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return AdvanceRequestSerializer
        elif self.action == 'list':
            return AdvanceListSerializer
        return AdvanceDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [CanRequestAdvance()]
        elif self.action in ['approve', 'reject']:
            return [CanApproveAdvance()]
        elif self.action == 'destroy':
            return [IsStaff()]
        return [CanViewAdvance()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Admin can see all advances
        if user.type == 'admin':
            return self.queryset

        # Receptionists can see their own advances
        if user.type == 'receptionist':
            return self.queryset.filter(receptionist=user)

        return self.queryset.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب السلف بنجاح / Advances retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل السلفة بنجاح / Advance details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        """Request advance (receptionist only)"""
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            advance = serializer.save()
            return created(
                message="تم إرسال طلب السلفة بنجاح / Advance request submitted successfully",
                data=AdvanceDetailSerializer(advance).data
            )

        return bad_request(
            message="فشل إرسال طلب السلفة / Failed to submit advance request",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != 'pending':
            return bad_request(
                message="يمكن حذف السلف المعلقة فقط / Can only delete pending advances"
            )

        instance.delete()
        return success(
            message="تم حذف طلب السلفة بنجاح / Advance request deleted successfully"
        )

    # ======================== Approval Actions ========================

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve advance request (admin only)"""
        advance = self.get_object()

        if advance.status != 'pending':
            return bad_request(
                message=f"لا يمكن الموافقة على سلفة بحالة '{advance.get_status_display()}' / Cannot approve advance with status '{advance.get_status_display()}'"
            )

        serializer = AdvanceApprovalSerializer(data=request.data)
        if serializer.is_valid():
            advance.status = 'approved'
            advance.approved_by = request.user
            advance.payment_date = serializer.validated_data.get('payment_date')

            notes = serializer.validated_data.get('notes', '')
            if notes:
                advance.notes = f"{advance.notes}\n{notes}" if advance.notes else notes

            advance.save()

            return success(
                message="تم الموافقة على السلفة بنجاح / Advance approved successfully",
                data=AdvanceDetailSerializer(advance).data
            )

        return bad_request(errors=serializer.errors)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject advance request (admin only)"""
        advance = self.get_object()

        if advance.status != 'pending':
            return bad_request(
                message=f"لا يمكن رفض سلفة بحالة '{advance.get_status_display()}' / Cannot reject advance with status '{advance.get_status_display()}'"
            )

        serializer = AdvanceApprovalSerializer(data=request.data)
        if serializer.is_valid():
            advance.status = 'rejected'
            advance.approved_by = request.user

            notes = serializer.validated_data.get('notes', '')
            if notes:
                advance.notes = f"{advance.notes}\n{notes}" if advance.notes else notes

            advance.save()

            return success(
                message="تم رفض السلفة / Advance rejected",
                data=AdvanceDetailSerializer(advance).data
            )

        return bad_request(errors=serializer.errors)

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def mark_paid(self, request, pk=None):
        """Mark advance as paid (admin only)"""
        advance = self.get_object()

        if advance.status != 'approved':
            return bad_request(
                message="يمكن دفع السلف الموافق عليها فقط / Can only pay approved advances"
            )

        if advance.status == 'paid':
            return bad_request(
                message="السلفة مدفوعة بالفعل / Advance is already paid"
            )

        advance.status = 'paid'
        advance.payment_date = date.today()
        advance.save()

        return success(
            message="تم تحديث حالة السلفة إلى مدفوع / Advance marked as paid",
            data=AdvanceDetailSerializer(advance).data
        )

    # ======================== Filtering Actions ========================

    @action(detail=False, methods=['get'])
    def my_advances(self, request):
        """Get current receptionist's advances"""
        if request.user.type != 'receptionist':
            return forbidden(
                message="هذا الإجراء متاح لموظفي الاستقبال فقط / This action is only available for receptionists"
            )

        queryset = self.get_queryset().filter(receptionist=request.user)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = AdvanceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdvanceListSerializer(queryset, many=True)
        return success(
            message="سلفك / Your advances",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending advances"""
        queryset = self.get_queryset().filter(status='pending')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = AdvanceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdvanceListSerializer(queryset, many=True)
        return success(
            message="السلف المعلقة / Pending advances",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get approved advances"""
        queryset = self.get_queryset().filter(status='approved')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = AdvanceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdvanceListSerializer(queryset, many=True)
        return success(
            message="السلف الموافق عليها / Approved advances",
            data=serializer.data
        )

    # ======================== Statistics Actions ========================

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get advance statistics (admin only)"""
        all_advances = self.queryset

        # Count by status
        status_counts = all_advances.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Calculate totals
        totals = all_advances.aggregate(
            total_amount=Sum('amount'),
            total_approved=Sum('amount', filter=Q(status__in=['approved', 'paid'])),
            total_paid=Sum('amount', filter=Q(status='paid'))
        )

        stats = {
            'total_advances': all_advances.count(),
            'pending_advances': status_dict.get('pending', 0),
            'approved_advances': status_dict.get('approved', 0),
            'rejected_advances': status_dict.get('rejected', 0),
            'paid_advances': status_dict.get('paid', 0),
            'total_amount': totals['total_amount'] or 0,
            'total_approved': totals['total_approved'] or 0,
            'total_paid': totals['total_paid'] or 0,
        }

        serializer = AdvanceStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات السلف / Advance statistics",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def receptionist_summary(self, request):
        """Get receptionist payroll summary (admin only)"""
        receptionist_id = request.query_params.get('receptionist')

        if not receptionist_id:
            return bad_request(
                message="معرف موظف الاستقبال مطلوب / Receptionist ID is required"
            )

        from accounts.models import CustomUser
        try:
            receptionist = CustomUser.objects.get(id=receptionist_id, type='receptionist')
        except CustomUser.DoesNotExist:
            return not_found(
                message="موظف الاستقبال غير موجود / Receptionist not found"
            )

        # Salary summary
        salaries = Salary.objects.filter(receptionist=receptionist)
        salary_total = salaries.aggregate(total=Sum('net_salary'))['total'] or 0

        # Advance summary
        advances = self.queryset.filter(receptionist=receptionist)
        advance_totals = advances.aggregate(
            total_amount=Sum('amount'),
            paid_amount=Sum('amount', filter=Q(status='paid'))
        )

        summary = {
            'receptionist_id': receptionist.id,
            'receptionist_name': receptionist.get_full_name(),
            'total_salaries': salaries.count(),
            'total_earned': salary_total,
            'total_advances': advances.count(),
            'total_advance_amount': advance_totals['total_amount'] or 0,
            'pending_advances': advances.filter(status='pending').count(),
        }

        serializer = ReceptionistPayrollSummarySerializer(data=summary)
        serializer.is_valid()

        return success(
            message=f"ملخص رواتب {receptionist.get_full_name()} / Payroll summary for {receptionist.get_full_name()}",
            data=serializer.data
        )