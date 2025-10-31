from django.db import models
from accounts.models import CustomUser
from etc.choices import BOOKING_STATUS_CHOICES


class Booking(models.Model):
    """
    Appointment bookings
    """
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_bookings',
        limit_choices_to={'type': 'patient'}
    )
    doctor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_bookings',
        limit_choices_to={'type': 'doctor'}
    )
    appointment_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['-appointment_datetime']

    def clean(self):
        """
        Validate that patient doesn't have multiple bookings on the same day
        """
        from django.core.exceptions import ValidationError
        from django.db.models import Q
        
        # Get the date only (without time)
        booking_date = self.appointment_datetime.date()
        
        # Check for existing bookings on the same day
        existing_bookings = Booking.objects.filter(
            patient=self.patient,
            appointment_datetime__date=booking_date
        ).exclude(
            status='cancelled'  # Don't count cancelled bookings
        )
        
        # If updating, exclude current booking
        if self.pk:
            existing_bookings = existing_bookings.exclude(pk=self.pk)
        
        if existing_bookings.exists():
            raise ValidationError(
                f'Patient already has a booking on {booking_date}. '
                f'Only one booking per day is allowed.'
            )
    
    def save(self, *args, **kwargs):
        """Override save to call clean()"""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {self.appointment_datetime}"
