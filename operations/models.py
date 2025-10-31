from django.db import models
from accounts.models import CustomUser
from etc.choices import OPERATION_STATUS_CHOICES, MEDIA_TYPE_CHOICES
from etc.helper_functions import operation_media_uploader

class Operation(models.Model):
    """
    Medical operations/procedures
    """
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_operations',
        limit_choices_to={'type': 'patient'}
    )
    doctor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_operations',
        limit_choices_to={'type': 'doctor'}
    )
    booking = models.OneToOneField(
        'appointments.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation'
    )
    operation_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    procedure_details = models.TextField(blank=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    operation_date = models.DateField()
    duration = models.TimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=OPERATION_STATUS_CHOICES,
        default='scheduled'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-operation_date']
    
    def __str__(self):
        return f"{self.operation_name} - {self.patient.get_full_name()}"


class OperationMedia(models.Model):
    """
    Media files for operations (xrays, images, videos)
    """
    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES
    )
    file_path = models.FileField(upload_to=operation_media_uploader)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_media_type_display()} - {self.file_name}"

