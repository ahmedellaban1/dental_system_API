from django.db import models
from accounts.models import CustomUser
from etc.choices import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES


class Bill(models.Model):
    """
    Patient bills
    """
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_bills',
        limit_choices_to={'type': 'patient'}
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bills',
        limit_choices_to={'type': 'receptionist'}
    )
    booking = models.ForeignKey(
        'appointments.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills'
    )
    operation = models.ForeignKey(
        'operations.operation',
        on_delete=models.CASCADE,
        related_name='bills'
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    remaining_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )
    bill_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-bill_date']
    
    @property
    def total_amount(self):
        """Get total amount from operation cost"""
        if self.operation and self.operation.cost:
            return self.operation.cost
        return 0
    
    def __str__(self):
        return f"Bill #{self.id} - {self.patient.get_full_name()} - {self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Get total amount from operation cost
        total_amount = 0
        if self.operation and self.operation.cost:
            total_amount = self.operation.cost
        
        # Auto-calculate remaining amount
        self.remaining_amount = total_amount - self.paid_amount
        
        # Auto-update payment status
        if self.remaining_amount <= 0:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
            
        super().save(*args, **kwargs)
