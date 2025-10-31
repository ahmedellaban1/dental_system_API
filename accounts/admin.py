from django.contrib import admin
from .models import CustomUser, Profile


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'type', 'email', 'is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('type', 'is_superuser', 'is_staff', 'is_active')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'gender')
    search_fields = ('city', 'gender')
    list_filter = ('gender',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)

