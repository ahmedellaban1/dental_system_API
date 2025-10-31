from django.db import models
from accounts.models import CustomUser
from etc.choices import FORM_CHOICES

class MedicineLibrary(models.Model):
    """
    Medicine library/database
    """    
    trade_name = models.CharField(max_length=200)
    active_ingredient = models.CharField(max_length=200)
    strength = models.CharField(max_length=50)  # e.g., "500mg"
    form = models.CharField(
        max_length=20,
        choices=FORM_CHOICES
    )
    description = models.TextField(blank=True)
    indications = models.TextField(blank=True)  
    contraindications = models.TextField(blank=True) 
    side_effects = models.TextField(blank=True)
    times_prescribed = models.IntegerField(default=0)      #يزيد تلقائي لوحده 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['trade_name', 'strength']
        ordering = ['trade_name']
    
    def __str__(self):
        return f"{self.trade_name} ({self.active_ingredient}) - {self.strength}"


class Prescription(models.Model):
    """
    Doctor's prescription
    """
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_prescriptions',
        limit_choices_to={'type': 'patient'}
    )
    doctor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_prescriptions',
        limit_choices_to={'type': 'doctor'}
    )
    booking = models.ForeignKey(
        'appointments.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions'
    )
    prescription_date = models.DateField(auto_now_add=True)
    diagnosis = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-prescription_date']
    
    def __str__(self):
        return f"Prescription for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()}"


class PrescriptionItem(models.Model):
    """
    Individual medicines in a prescription
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    medicine = models.ForeignKey(
        MedicineLibrary,
        on_delete=models.PROTECT,
        related_name='prescription_items'
    )
    dosage = models.CharField(max_length=100)  # e.g., "500mg"
    frequency = models.CharField(max_length=100)  # e.g., "3 times daily"
    duration_days = models.IntegerField()
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.medicine.trade_name} - {self.dosage}"
    
    def save(self, *args, **kwargs):
        # Increment times_prescribed counter
        if not self.pk:  # Only on creation
            self.medicine.times_prescribed += 1
            self.medicine.save()
        super().save(*args, **kwargs)

