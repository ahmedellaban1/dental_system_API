from django.db import models
from etc.choices import CATEGORY_CHOICES
from accounts.models import CustomUser


class CommonDisease(models.Model):
    """
    Library of common diseases
    """
    disease_name_ar = models.CharField(max_length=200)
    disease_name_en = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    symptoms = models.TextField(blank=True)
    common_treatments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __str__(self):
        return f"{self.disease_name_ar} ({self.disease_name_en})"



class ChronicDisease(models.Model):
    """
    Patient's chronic diseases
    """
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chronic_diseases',
        limit_choices_to={'type': 'patient'}
    )
    disease = models.ForeignKey(
        CommonDisease,
        on_delete=models.PROTECT,
        related_name='patient_cases'
    )
    description = models.TextField(blank=True)
    diagnosed_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'disease']
        ordering = ['-diagnosed_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.disease.disease_name_ar}"
