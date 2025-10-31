from django.contrib import admin
from .models import Booking


class BookingAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'status', 'created_at')
    search_fields = ('created_at', )
    list_filter = ('status', )


admin.site.register(Booking, BookingAdmin)

