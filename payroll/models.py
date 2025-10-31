from django.db import models
from accounts.models import CustomUser
from etc.choices import SALARY_STATUS_CHOICES, ADVANCE_STATUS_CHOICES


class Salary(models.Model):
    """
    Receptionist salaries
    """    
    receptionist = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='salaries',
        limit_choices_to={'type': 'receptionist'}
    )
    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    salary_month = models.DateField()  # First day of the month
    payment_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=SALARY_STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['receptionist', 'salary_month']
        ordering = ['-salary_month']
    
    def __str__(self):
        return f"Salary for {self.receptionist.get_full_name()} - {self.salary_month.strftime('%B %Y')}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate net salary
        self.net_salary = self.base_salary + self.bonus - self.deductions
        super().save(*args, **kwargs)


class Advance(models.Model):
    """
    Salary advances for receptionists
    """
    receptionist = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='advances',
        limit_choices_to={'type': 'receptionist'}
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    request_date = models.DateField(auto_now_add=True)
    payment_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=ADVANCE_STATUS_CHOICES,
        default='pending'
    )
    reason = models.TextField()
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_advances',
        limit_choices_to={'type__in': ['doctor', 'receptionist']}
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'advances'
        verbose_name = 'Advance'
        verbose_name_plural = 'Advances'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Advance {self.amount} for {self.receptionist.get_full_name()} - {self.get_status_display()}"