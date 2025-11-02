"""
=============================================================================
billing/views.py - Billing & Payment Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
from datetime import datetime, timedelta

from .models import Bill
from .serializers import (
    BillListSerializer, BillDetailSerializer,
    BillCreateSerializer, BillUpdateSerializer,
    PaymentSerializer, BillSummarySerializer,
    PatientBillSummarySerializer, PaymentMethodStatsSerializer,
    MonthlyRevenueSerializer
)
from etc.permissions import (
    CanViewBill, CanCreateBill, CanUpdateBill,
    CanProcessPayment, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class BillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient bills
    - List: Staff see all, Patients see own
    - Create: Staff only
    - Update: Staff only
    - Delete: Admin only
    """
    queryset = Bill.objects.select_related(
        'patient', 'created_by', 'booking', 'operation',
        'patient__user_profile', 'created_by__user_profile'
    ).all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'payment_method', 'patient', 'operation']
    search_fields = ['patient__first_name', 'patient__last_name', 'notes']
    ordering_fields = ['bill_date', 'due_date', 'total_amount', 'remaining_amount', 'payment_status']
    ordering = ['-bill_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return BillCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BillUpdateSerializer
        elif self.action == 'list':
            return BillListSerializer
        return BillDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [CanCreateBill()]
        elif self.action in ['update', 'partial_update']:
            return [CanUpdateBill()]
        elif self.action == 'destroy':
            return [IsStaff()]
        elif self.action == 'process_payment':
            return [CanProcessPayment()]
        return [CanViewBill()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Staff can see all bills
        if user.type in ['admin', 'receptionist']:
            return self.queryset

        # Patients can see their own bills
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
            message="تم جلب الفواتير بنجاح / Bills retrieved successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب تفاصيل الفاتورة بنجاح / Bill details retrieved successfully",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            bill = serializer.save()
            return created(
                message="تم إنشاء الفاتورة بنجاح / Bill created successfully",
                data=BillDetailSerializer(bill).data
            )

        return bad_request(
            message="فشل إنشاء الفاتورة / Failed to create bill",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)

        if serializer.is_valid():
            bill = serializer.save()
            return success(
                message="تم تحديث الفاتورة بنجاح / Bill updated successfully",
                data=BillDetailSerializer(bill).data
            )

        return bad_request(
            message="فشل تحديث الفاتورة / Failed to update bill",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            bill = serializer.save()
            return success(
                message="تم تحديث الفاتورة بنجاح / Bill updated successfully",
                data=BillDetailSerializer(bill).data
            )

        return bad_request(
            message="فشل تحديث الفاتورة / Failed to update bill",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف الفاتورة بنجاح / Bill deleted successfully"
        )

    # ======================== Payment Actions ========================

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process payment for a bill"""
        bill = self.get_object()

        if bill.payment_status == 'paid':
            return bad_request(
                message="الفاتورة مدفوعة بالكامل بالفعل / Bill is already fully paid"
            )

        serializer = PaymentSerializer(data=request.data, instance=bill)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method = serializer.validated_data['payment_method']
            notes = serializer.validated_data.get('notes', '')

            # Update bill
            bill.paid_amount += amount
            bill.payment_method = payment_method
            if notes:
                bill.notes = f"{bill.notes}\n{notes}" if bill.notes else notes
            bill.save()

            return success(
                message="تم تسجيل الدفع بنجاح / Payment processed successfully",
                data=BillDetailSerializer(bill).data
            )

        return bad_request(
            message="فشل معالجة الدفع / Payment processing failed",
            errors=serializer.errors
        )

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def mark_paid(self, request, pk=None):
        """Mark bill as fully paid (staff only)"""
        bill = self.get_object()

        if bill.payment_status == 'paid':
            return bad_request(
                message="الفاتورة مدفوعة بالكامل بالفعل / Bill is already fully paid"
            )

        # Set paid amount to total amount
        bill.paid_amount = bill.total_amount
        bill.save()

        return success(
            message="تم تحديث حالة الفاتورة إلى مدفوع / Bill marked as paid",
            data=BillDetailSerializer(bill).data
        )

    # ======================== Filtering Actions ========================

    @action(detail=False, methods=['get'])
    def my_bills(self, request):
        """Get current patient's bills"""
        if request.user.type != 'patient':
            return forbidden(
                message="هذا الإجراء متاح للمرضى فقط / This action is only available for patients"
            )

        queryset = self.get_queryset().filter(patient=request.user)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BillListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BillListSerializer(queryset, many=True)
        return success(
            message="تم جلب فواتيرك بنجاح / Your bills retrieved successfully",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """Get unpaid bills"""
        queryset = self.get_queryset().filter(payment_status='unpaid')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BillListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BillListSerializer(queryset, many=True)
        return success(
            message="الفواتير غير المدفوعة / Unpaid bills",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def partial(self, request):
        """Get partially paid bills"""
        queryset = self.get_queryset().filter(payment_status='partial')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BillListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BillListSerializer(queryset, many=True)
        return success(
            message="الفواتير المدفوعة جزئياً / Partially paid bills",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue bills"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            due_date__lt=today,
            payment_status__in=['unpaid', 'partial']
        )
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BillListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BillListSerializer(queryset, many=True)
        return success(
            message="الفواتير المتأخرة / Overdue bills",
            data=serializer.data
        )

    # ======================== Statistics Actions ========================

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def summary(self, request):
        """Get billing summary statistics (staff only)"""
        all_bills = self.queryset
        today = timezone.now().date()

        # Calculate totals
        totals = all_bills.aggregate(
            total_amount=Sum(F('operation__cost')),
            total_paid=Sum('paid_amount'),
            total_remaining=Sum('remaining_amount')
        )

        # Count by status
        status_counts = all_bills.values('payment_status').annotate(count=Count('id'))
        status_dict = {item['payment_status']: item['count'] for item in status_counts}

        # Count overdue
        overdue_count = all_bills.filter(
            due_date__lt=today,
            payment_status__in=['unpaid', 'partial']
        ).count()

        summary = {
            'total_bills': all_bills.count(),
            'total_amount': totals['total_amount'] or 0,
            'total_paid': totals['total_paid'] or 0,
            'total_remaining': totals['total_remaining'] or 0,
            'unpaid_bills': status_dict.get('unpaid', 0),
            'partial_bills': status_dict.get('partial', 0),
            'paid_bills': status_dict.get('paid', 0),
            'overdue_bills': overdue_count,
        }

        serializer = BillSummarySerializer(data=summary)
        serializer.is_valid()

        return success(
            message="ملخص الفواتير / Billing summary",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_patient(self, request):
        """Get bill summary grouped by patient (staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب / Patient ID is required"
            )

        bills = self.queryset.filter(patient_id=patient_id)

        if not bills.exists():
            return success(
                message="لا توجد فواتير لهذا المريض / No bills found for this patient",
                data={}
            )

        # Calculate summary
        patient = bills.first().patient
        totals = bills.aggregate(
            total_amount=Sum(F('operation__cost')),
            total_paid=Sum('paid_amount'),
            total_remaining=Sum('remaining_amount')
        )

        status_counts = bills.values('payment_status').annotate(count=Count('id'))
        status_dict = {item['payment_status']: item['count'] for item in status_counts}

        summary = {
            'patient_id': patient.id,
            'patient_name': patient.get_full_name(),
            'total_bills': bills.count(),
            'total_amount': totals['total_amount'] or 0,
            'total_paid': totals['total_paid'] or 0,
            'total_remaining': totals['total_remaining'] or 0,
            'unpaid_count': status_dict.get('unpaid', 0),
            'partial_count': status_dict.get('partial', 0),
            'paid_count': status_dict.get('paid', 0),
        }

        serializer = PatientBillSummarySerializer(data=summary)
        serializer.is_valid()

        return success(
            message=f"ملخص فواتير {patient.get_full_name()} / Bill summary for {patient.get_full_name()}",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def payment_methods(self, request):
        """Get statistics by payment method (staff only)"""
        from etc.choices import PAYMENT_METHOD_CHOICES

        stats = self.queryset.filter(
            payment_status__in=['partial', 'paid']
        ).values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('paid_amount')
        ).order_by('-total_amount')

        # Add display names
        method_dict = dict(PAYMENT_METHOD_CHOICES)
        results = []
        for stat in stats:
            if stat['payment_method']:
                results.append({
                    'payment_method': stat['payment_method'],
                    'payment_method_display': method_dict.get(stat['payment_method'], stat['payment_method']),
                    'count': stat['count'],
                    'total_amount': stat['total_amount'] or 0
                })

        serializer = PaymentMethodStatsSerializer(data=results, many=True)
        serializer.is_valid()

        return success(
            message="إحصائيات طرق الدفع / Payment method statistics",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def monthly_revenue(self, request):
        """Get monthly revenue statistics (staff only)"""
        from django.db.models.functions import TruncMonth

        # Get last 12 months
        revenue_data = self.queryset.annotate(
            month=TruncMonth('bill_date')
        ).values('month').annotate(
            total_billed=Sum(F('operation__cost')),
            total_collected=Sum('paid_amount'),
            total_pending=Sum('remaining_amount'),
            bill_count=Count('id')
        ).order_by('-month')[:12]

        results = []
        for data in revenue_data:
            results.append({
                'month': data['month'].strftime('%B'),
                'year': data['month'].year,
                'total_billed': data['total_billed'] or 0,
                'total_collected': data['total_collected'] or 0,
                'total_pending': data['total_pending'] or 0,
                'bill_count': data['bill_count']
            })

        serializer = MonthlyRevenueSerializer(data=results, many=True)
        serializer.is_valid()

        return success(
            message="الإيرادات الشهرية / Monthly revenue",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def today_revenue(self, request):
        """Get today's revenue (staff only)"""
        today = timezone.now().date()
        today_bills = self.queryset.filter(bill_date=today)

        totals = today_bills.aggregate(
            total_billed=Sum(F('operation__cost')),
            total_collected=Sum('paid_amount'),
            count=Count('id')
        )

        return success(
            message=f"إيرادات اليوم ({today}) / Today's revenue ({today})",
            data={
                'date': today,
                'total_billed': totals['total_billed'] or 0,
                'total_collected': totals['total_collected'] or 0,
                'bill_count': totals['count']
            }
        )