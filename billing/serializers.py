"""
=============================================================================
billing/serializers.py - Billing & Payment Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from .models import Bill
from accounts.models import CustomUser
from appointments.models import Booking
from etc.validators import validate_positive_number


# ======================== Nested Serializers ========================

class PatientBillSerializer(serializers.ModelSerializer):
    """
    Minimal patient info for bills
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


class ReceptionistSerializer(serializers.ModelSerializer):
    """
    Minimal receptionist info for bills
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name']
        read_only_fields = fields


class BookingBillSerializer(serializers.ModelSerializer):
    """
    Minimal booking info for bills
    """
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'appointment_datetime', 'doctor_name', 'status']
        read_only_fields = fields


class OperationBillSerializer(serializers.ModelSerializer):
    """
    Minimal operation info for bills
    """
    operation_name = serializers.CharField(source='name', read_only=True)
    operation_cost = serializers.DecimalField(source='cost', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        from operations.models import Operation
        model = Operation
        fields = ['id', 'operation_name', 'operation_cost', 'status']
        read_only_fields = fields


# ======================== Bill Serializers ========================

class BillListSerializer(serializers.ModelSerializer):
    """
    Minimal bill serializer for lists
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'patient', 'patient_name', 'total_amount',
            'paid_amount', 'remaining_amount', 'payment_status',
            'payment_status_display', 'payment_method', 'payment_method_display',
            'bill_date', 'due_date'
        ]
        read_only_fields = ['id', 'bill_date', 'remaining_amount', 'payment_status']


class BillDetailSerializer(serializers.ModelSerializer):
    """
    Detailed bill serializer with nested relations
    """
    patient_details = PatientBillSerializer(source='patient', read_only=True)
    created_by_details = ReceptionistSerializer(source='created_by', read_only=True)
    booking_details = BookingBillSerializer(source='booking', read_only=True)
    operation_details = OperationBillSerializer(source='operation', read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'patient', 'patient_details', 'created_by', 'created_by_details',
            'booking', 'booking_details', 'operation', 'operation_details',
            'total_amount', 'paid_amount', 'remaining_amount',
            'payment_status', 'payment_status_display',
            'payment_method', 'payment_method_display',
            'bill_date', 'due_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'bill_date', 'remaining_amount',
            'payment_status', 'created_at', 'updated_at'
        ]


class BillCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating bills
    """

    class Meta:
        model = Bill
        fields = [
            'patient', 'booking', 'operation',
            'paid_amount', 'payment_method', 'due_date', 'notes'
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

    def validate_operation(self, value):
        """Validate operation exists and has cost"""
        if not value.cost or value.cost <= 0:
            raise serializers.ValidationError(
                "العملية يجب أن يكون لها تكلفة محددة / Operation must have a valid cost"
            )
        return value

    def validate_paid_amount(self, value):
        """Validate paid amount is not negative"""
        if value < 0:
            raise serializers.ValidationError(
                "المبلغ المدفوع لا يمكن أن يكون سالباً / Paid amount cannot be negative"
            )
        return value

    def validate(self, attrs):
        """Validate paid amount doesn't exceed total"""
        operation = attrs.get('operation')
        paid_amount = attrs.get('paid_amount', 0)

        if operation and operation.cost:
            if paid_amount > operation.cost:
                raise serializers.ValidationError({
                    'paid_amount': f'المبلغ المدفوع ({paid_amount}) يتجاوز التكلفة الإجمالية ({operation.cost}) / Paid amount exceeds total cost'
                })

        # Validate booking belongs to patient if provided
        booking = attrs.get('booking')
        patient = attrs.get('patient')
        if booking and booking.patient != patient:
            raise serializers.ValidationError({
                'booking': 'الحجز لا يخص هذا المريض / Booking does not belong to this patient'
            })

        return attrs

    def create(self, validated_data):
        """Create bill with created_by from request user"""
        request = self.context.get('request')
        if request and request.user.type in ['admin', 'receptionist']:
            validated_data['created_by'] = request.user

        return super().create(validated_data)


class BillUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating bills
    """

    class Meta:
        model = Bill
        fields = [
            'paid_amount', 'payment_method', 'due_date', 'notes'
        ]

    def validate_paid_amount(self, value):
        """Validate paid amount"""
        if value < 0:
            raise serializers.ValidationError(
                "المبلغ المدفوع لا يمكن أن يكون سالباً / Paid amount cannot be negative"
            )

        # Check doesn't exceed total
        instance = self.instance
        if instance.operation and instance.operation.cost:
            if value > instance.operation.cost:
                raise serializers.ValidationError(
                    f'المبلغ المدفوع ({value}) يتجاوز التكلفة الإجمالية ({instance.operation.cost}) / Paid amount exceeds total cost'
                )

        return value


class PaymentSerializer(serializers.Serializer):
    """
    Serializer for processing payments
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'card', 'vodafone_cash', 'instapay', 'transfer'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        """Validate payment amount"""
        if value <= 0:
            raise serializers.ValidationError(
                "المبلغ يجب أن يكون أكبر من صفر / Amount must be greater than zero"
            )

        # Check doesn't exceed remaining amount
        instance = self.instance
        if instance and instance.remaining_amount:
            if value > instance.remaining_amount:
                raise serializers.ValidationError(
                    f'المبلغ ({value}) يتجاوز المبلغ المتبقي ({instance.remaining_amount}) / Amount exceeds remaining balance'
                )

        return value


class BillSummarySerializer(serializers.Serializer):
    """
    Serializer for bill summary/statistics
    """
    total_bills = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=12, decimal_places=2)
    unpaid_bills = serializers.IntegerField()
    partial_bills = serializers.IntegerField()
    paid_bills = serializers.IntegerField()
    overdue_bills = serializers.IntegerField()


class PatientBillSummarySerializer(serializers.Serializer):
    """
    Serializer for patient-specific bill summary
    """
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    total_bills = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=12, decimal_places=2)
    unpaid_count = serializers.IntegerField()
    partial_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()


class PaymentMethodStatsSerializer(serializers.Serializer):
    """
    Serializer for payment method statistics
    """
    payment_method = serializers.CharField()
    payment_method_display = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class MonthlyRevenueSerializer(serializers.Serializer):
    """
    Serializer for monthly revenue statistics
    """
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_billed = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=12, decimal_places=2)
    bill_count = serializers.IntegerField()