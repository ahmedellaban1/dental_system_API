from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from cities_light.models import City
from etc.choices import USER_TYPE_CHOICES, GENDER_CHOICES
from etc.helper_functions import profile_image_uploader
from datetime import timedelta  


class CustomUser(AbstractUser):
    """
    Custom User Model with role-based access
    """
    type = models.CharField(max_length=12, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.type}"


class Profile(models.Model):
    """
    User Profile - One-to-One with User
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile', primary_key=True)
    image = models.ImageField(upload_to=profile_image_uploader, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, default=None, help_text="Format: YYYY-MM-DD")
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @receiver(post_save, sender=CustomUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    def __str__(self):
        return f"{self.user.username}'s profile"
