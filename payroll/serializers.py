"""
=============================================================================
payroll/serializers.py - Payroll & Salary Management Serializers
=============================================================================
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from .models import Salary, Advance
from accounts.models import CustomUser
from etc.validators import validate_positive_number


# ======================== Nested User Serializers ========================

class ReceptionistPayrollSerializer(serializers.ModelSerializer):
    """
    Minimal receptionist info for payroll
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    phone = serializers.CharField(source='user_profile.phone', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'phone']
        read_only_fields = fields


class ApproverSerializer(serializers.ModelSerializer):
    """
    Minimal approver info
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name']
        read_only_fields = fields


# ======================== Salary Serializers ========================

class SalaryListSerializer(serializers.ModelSerializer):
    """
    Minimal salary serializer for lists
    """
    receptionist_name = serializers.CharField(source='receptionist.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    month_display = serializers.SerializerMethodField()

    class Meta:
        model = Salary
        fields = [
            'id', 'receptionist', 'receptionist_name', 'base_salary',
            'bonus', 'deductions', 'net_salary', 'salary_month',
            'month_display', 'payment_date', 'status', 'status_display',
            'created_at'
        ]
        read_only_fields = ['id', 'net_salary', 'created_at']

    def get_month_display(self, obj):
        """Format month as 'Month YYYY'"""
        return obj.salary_month.strftime('%B %Y')


class SalaryDetailSerializer(serializers.ModelSerializer):
    """
    Detailed salary serializer with nested relations
    """
    receptionist_details = ReceptionistPayrollSerializer(source='receptionist', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    month_display = serializers.SerializerMethodField()

    class Meta:
        model = Salary
        fields = [
            'id', 'receptionist', 'receptionist_details', 'base_salary',
            'bonus', 'deductions', 'net_salary', 'salary_month',
            'month_display', 'payment_date', 'status', 'status_display',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'net_salary', 'created_at', 'updated_at']

    def get_month_display(self, obj):
        """Format month as 'Month YYYY'"""
        return obj.salary_month.strftime('%B %Y')


class SalaryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating salary records
    """

    class Meta:
        model = Salary
        fields = [
            'receptionist', 'base_salary', 'bonus', 'deductions',
            'salary_month', 'payment_date', 'status', 'notes'
        ]

    def validate_receptionist(self, value):
        """Validate receptionist exists and is active"""
        if value.type != 'receptionist':
            raise serializers.ValidationError(
                "المستخدم المحدد ليس موظف استقبال / Selected user is not a receptionist"
            )
        if not value.is_active:
            raise serializers.ValidationError(
                "حساب موظف الاستقبال غير مفعل / Receptionist account is inactive"
            )
        return value

    def validate_base_salary(self, value):
        """Validate base salary is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "الراتب الأساسي يجب أن يكون أكبر من صفر / Base salary must be greater than zero"
            )
        return value

    def validate_bonus(self, value):
        """Validate bonus is non-negative"""
        if value < 0:
            raise serializers.ValidationError(
                "المكافأة لا يمكن أن تكون سالبة / Bonus cannot be negative"
            )
        return value

    def validate_deductions(self, value):
        """Validate deductions is non-negative"""
        if value < 0:
            raise serializers.ValidationError(
                "الخصومات لا يمكن أن تكون سالبة / Deductions cannot be negative"
            )
        return value

    def validate_salary_month(self, value):
        """Ensure salary_month is first day of month"""
        if value.day != 1:
            # Auto-correct to first day of month
            from datetime import date
            value = date(value.year, value.month, 1)
        return value

    def validate(self, attrs):
        """Check for duplicate salary for same month"""
        receptionist = attrs.get('receptionist')
        salary_month = attrs.get('salary_month')

        # Check if updating
        instance = self.instance

        if receptionist and salary_month:
            existing = Salary.objects.filter(
                receptionist=receptionist,
                salary_month=salary_month
            )
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'salary_month': f'راتب موظف الاستقبال لشهر {salary_month.strftime("%B %Y")} موجود بالفعل / Salary for {salary_month.strftime("%B %Y")} already exists'
                })

        # Validate net salary won't be negative
        base = attrs.get('base_salary', 0)
        bonus = attrs.get('bonus', 0)
        deductions = attrs.get('deductions', 0)

        if (base + bonus - deductions) < 0:
            raise serializers.ValidationError(
                "الراتب الصافي لا يمكن أن يكون سالباً / Net salary cannot be negative"
            )

        return attrs


class SalaryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating salary records
    Cannot change receptionist or month
    """

    class Meta:
        model = Salary
        fields = ['base_salary', 'bonus', 'deductions', 'payment_date', 'status', 'notes']

    def validate_base_salary(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "الراتب الأساسي يجب أن يكون أكبر من صفر / Base salary must be greater than zero"
            )
        return value

    def validate_bonus(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "المكافأة لا يمكن أن تكون سالبة / Bonus cannot be negative"
            )
        return value

    def validate_deductions(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "الخصومات لا يمكن أن تكون سالبة / Deductions cannot be negative"
            )
        return value

    def validate(self, attrs):
        """Validate net salary won't be negative"""
        instance = self.instance
        base = attrs.get('base_salary', instance.base_salary)
        bonus = attrs.get('bonus', instance.bonus)
        deductions = attrs.get('deductions', instance.deductions)

        if (base + bonus - deductions) < 0:
            raise serializers.ValidationError(
                "الراتب الصافي لا يمكن أن يكون سالباً / Net salary cannot be negative"
            )

        return attrs


class SalaryPaymentSerializer(serializers.Serializer):
    """
    Serializer for processing salary payment
    """
    payment_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


# ======================== Advance Serializers ========================

class AdvanceListSerializer(serializers.ModelSerializer):
    """
    Minimal advance serializer for lists
    """
    receptionist_name = serializers.CharField(source='receptionist.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = Advance
        fields = [
            'id', 'receptionist', 'receptionist_name', 'amount',
            'request_date', 'payment_date', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'request_date', 'created_at']


class AdvanceDetailSerializer(serializers.ModelSerializer):
    """
    Detailed advance serializer with nested relations
    """
    receptionist_details = ReceptionistPayrollSerializer(source='receptionist', read_only=True)
    approved_by_details = ApproverSerializer(source='approved_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Advance
        fields = [
            'id', 'receptionist', 'receptionist_details', 'amount',
            'request_date', 'payment_date', 'status', 'status_display',
            'reason', 'approved_by', 'approved_by_details', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'request_date', 'approved_by', 'created_at', 'updated_at']


class AdvanceRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for requesting advance (receptionist)
    """

    class Meta:
        model = Advance
        fields = ['amount', 'reason']

    def validate_amount(self, value):
        """Validate advance amount is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "المبلغ يجب أن يكون أكبر من صفر / Amount must be greater than zero"
            )
        return value

    def validate_reason(self, value):
        """Validate reason is not empty"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "السبب يجب أن يكون 10 أحرف على الأقل / Reason must be at least 10 characters"
            )
        return value.strip()

    def create(self, validated_data):
        """Create advance request with receptionist from context"""
        request = self.context.get('request')
        if request and request.user.type == 'receptionist':
            validated_data['receptionist'] = request.user
            validated_data['status'] = 'pending'
        return super().create(validated_data)


class AdvanceApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving/rejecting advances
    """
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_date = serializers.DateField(required=False)


# ======================== Statistics Serializers ========================

class SalaryStatsSerializer(serializers.Serializer):
    """
    Serializer for salary statistics
    """
    total_salaries = serializers.IntegerField()
    pending_salaries = serializers.IntegerField()
    partial_salaries = serializers.IntegerField()
    paid_salaries = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class AdvanceStatsSerializer(serializers.Serializer):
    """
    Serializer for advance statistics
    """
    total_advances = serializers.IntegerField()
    pending_advances = serializers.IntegerField()
    approved_advances = serializers.IntegerField()
    rejected_advances = serializers.IntegerField()
    paid_advances = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_approved = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)


class ReceptionistPayrollSummarySerializer(serializers.Serializer):
    """
    Serializer for receptionist payroll summary
    """
    receptionist_id = serializers.IntegerField()
    receptionist_name = serializers.CharField()
    total_salaries = serializers.IntegerField()
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_advances = serializers.IntegerField()
    total_advance_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_advances = serializers.IntegerField()