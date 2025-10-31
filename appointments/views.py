"""
=============================================================================
appointments/views.py - Appointment Booking Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import Booking
from .serializers import (
    BookingListSerializer, BookingDetailSerializer,
    BookingCreateSerializer, BookingUpdateSerializer,
    BookingStatusUpdateSerializer, BookingCancelSerializer,
    BookingStatsSerializer
)
from etc.permissions import (
    CanViewBooking, CanCreateBooking, CanUpdateBooking,
    CanCancelBooking, IsStaff
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointment bookings
    - List: User-specific (patients see own, doctors see own, staff see all)
    - Create: Admin, Receptionist (any patient), Patient (self only)
    - Update: Admin, Receptionist (all), Doctor (own, status/notes), Patient (own pending, reason only)
    - Delete: Admin only
    """
    queryset = Booking.objects.select_related('patient', 'doctor', 'patient__user_profile',
                                              'doctor__user_profile').all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'doctor', 'patient', 'appointment_datetime']
    search_fields = ['patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name', 'reason']
    ordering_fields = ['appointment_datetime', 'created_at', 'status']
    ordering = ['-appointment_datetime']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [CanCreateBooking()]
        elif self.action in ['update', 'partial_update']:
            return [CanUpdateBooking()]
        elif self.action == 'destroy':
            return [IsStaff()]
        elif self.action in ['cancel', 'confirm', 'complete']:
            return [CanCancelBooking()]
        return [CanViewBooking()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        # Staff can see all bookings
        if user.type in ['admin', 'receptionist']:
            return self.queryset

        # Doctors can see their bookings
        if user.type == 'doctor':
            return self.queryset.filter(doctor=user)

        # Patients can see their bookings
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
            message="تم استرجاع الحجوزات بنجاح",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم استرجاع تفاصيل الحجز بنجاح",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            booking = serializer.save()
            return created(
                message="تم إنشاء الحجز بنجاح",
                data=BookingDetailSerializer(booking).data
            )

        return bad_request(
            message="فشل إنشاء الحجز",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False, context={'request': request})

        if serializer.is_valid():
            booking = serializer.save()
            return success(
                message="تم تحديث الحجز بنجاح",
                data=BookingDetailSerializer(booking).data
            )

        return bad_request(
            message="فشل تحديث الحجز",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            booking = serializer.save()
            return success(
                message="تم تحديث الحجز بنجاح",
                data=BookingDetailSerializer(booking).data
            )

        return bad_request(
            message="فشل تحديث الحجز",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف الحجز بنجاح"
        )

    # ======================== Custom Actions ========================

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()

        if booking.status == 'cancelled':
            return bad_request(
                message="الحجز ملغي بالفعل"
            )

        if booking.status == 'completed':
            return bad_request(
                message="لا يمكن إلغاء حجز مكتمل"
            )

        serializer = BookingCancelSerializer(data=request.data)
        if serializer.is_valid():
            booking.status = 'cancelled'
            if serializer.validated_data.get('reason'):
                booking.notes = f"سبب الإلغاء: {serializer.validated_data['reason']}"
            booking.save()

            return success(
                message="تم إلغاء الحجز بنجاح",
                data=BookingDetailSerializer(booking).data
            )

        return bad_request(errors=serializer.errors)

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def confirm(self, request, pk=None):
        """Confirm a pending booking (Staff only)"""
        booking = self.get_object()

        if booking.status != 'pending':
            return bad_request(
                message=f"لا يمكن تأكيد حجز بحالة '{booking.get_status_display()}' / Cannot confirm booking with status '{booking.get_status_display()}'"
            )

        booking.status = 'confirmed'
        booking.save()

        return success(
            message="تم تأكيد الحجز بنجاح",
            data=BookingDetailSerializer(booking).data
        )

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def complete(self, request, pk=None):
        """Mark booking as completed (Staff only)"""
        booking = self.get_object()

        if booking.status == 'cancelled':
            return bad_request(
                message="لا يمكن إكمال حجز ملغي"
            )

        if booking.status == 'completed':
            return bad_request(
                message="الحجز مكتمل بالفعل"
            )

        booking.status = 'completed'
        booking.save()

        return success(
            message="تم تحديث حالة الحجز إلى مكتمل",
            data=BookingDetailSerializer(booking).data
        )

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get current user's bookings"""
        user = request.user

        if user.type == 'patient':
            queryset = self.queryset.filter(patient=user)
        elif user.type == 'doctor':
            queryset = self.queryset.filter(doctor=user)
        else:
            queryset = self.queryset

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message="تم استرجاع حجوزاتك بنجاح",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's bookings"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            appointment_datetime__date=today
        ).exclude(status='cancelled')

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message=f"حجوزات اليوم ({today}) / Today's bookings ({today})",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings (next 7 days)"""
        today = timezone.now()
        next_week = today + timedelta(days=7)

        queryset = self.get_queryset().filter(
            appointment_datetime__gte=today,
            appointment_datetime__lte=next_week
        ).exclude(status='cancelled')

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message="الحجوزات القادمة (7 أيام)",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get past bookings"""
        today = timezone.now()

        queryset = self.get_queryset().filter(
            appointment_datetime__lt=today
        )

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message="الحجوزات السابقة",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def statistics(self, request):
        """Get booking statistics (Staff only)"""
        today = timezone.now().date()

        all_bookings = self.queryset

        stats = {
            'total_bookings': all_bookings.count(),
            'pending_bookings': all_bookings.filter(status='pending').count(),
            'confirmed_bookings': all_bookings.filter(status='confirmed').count(),
            'completed_bookings': all_bookings.filter(status='completed').count(),
            'cancelled_bookings': all_bookings.filter(status='cancelled').count(),
            'today_bookings': all_bookings.filter(
                appointment_datetime__date=today
            ).exclude(status='cancelled').count(),
            'upcoming_bookings': all_bookings.filter(
                appointment_datetime__gte=timezone.now()
            ).exclude(status='cancelled').count(),
        }

        serializer = BookingStatsSerializer(data=stats)
        serializer.is_valid()

        return success(
            message="إحصائيات الحجوزات",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_doctor(self, request):
        """Get bookings grouped by doctor (Staff only)"""
        doctor_id = request.query_params.get('doctor')

        if not doctor_id:
            return bad_request(
                message="معرف الطبيب مطلوب"
            )

        queryset = self.queryset.filter(doctor_id=doctor_id)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message="حجوزات الطبيب",
            data=serializer.data
        )

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def by_patient(self, request):
        """Get bookings grouped by patient (Staff only)"""
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return bad_request(
                message="معرف المريض مطلوب"
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return success(
            message="حجوزات المريض",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a doctor on a specific date"""
        doctor_id = request.query_params.get('doctor')
        date_str = request.query_params.get('date')  # Format: YYYY-MM-DD

        if not doctor_id or not date_str:
            return bad_request(
                message="معرف الطبيب والتاريخ مطلوبان"
            )

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return bad_request(
                message="تنسيق التاريخ غير صحيح. استخدم YYYY-MM-DD"
            )

        # Check if date is in the past
        if date < timezone.now().date():
            return bad_request(
                message="لا يمكن الحجز في تاريخ سابق"
            )

        # Check if Friday
        if date.weekday() == 4:
            return success(
                message="لا توجد مواعيد متاحة يوم الجمعة",
                data={'available_slots': []}
            )

        # Get existing bookings for this doctor on this date
        existing_bookings = Booking.objects.filter(
            doctor_id=doctor_id,
            appointment_datetime__date=date
        ).exclude(status='cancelled').values_list('appointment_datetime', flat=True)

        # Generate available slots (8 AM - 8 PM, 30-minute intervals)
        available_slots = []
        start_hour = 8
        end_hour = 20

        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                slot_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                slot_time = timezone.make_aware(slot_time)

                # Check if slot is not booked
                if slot_time not in existing_bookings:
                    # Check if slot is in the future (for today)
                    if slot_time > timezone.now():
                        available_slots.append(slot_time.strftime('%Y-%m-%d %H:%M:%S'))

        return success(
            message=f"المواعيد المتاحة في {date} / Available slots on {date}",
            data={'available_slots': available_slots, 'count': len(available_slots)}
        )