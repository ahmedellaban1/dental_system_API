from django.contrib import admin
from .models import Bill


class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'created_by', 'booking', 'operation')
    search_fields = ('created_at', 'bill_date')


admin.site.register(Bill, BillAdmin)

