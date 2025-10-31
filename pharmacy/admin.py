from django.contrib import admin
from .models import MedicineLibrary,Prescription,PrescriptionItem


class MedicineLibraryAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'active_ingredient', 'strength')
    search_fields = ('trade_name', 'active_ingredient')
    list_filter = ('active_ingredient', )


class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'prescription_date')
    list_filter = ('created_at', )


class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medicine', 'frequency')
    list_filter = ('created_at', )


admin.site.register(MedicineLibrary, MedicineLibraryAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(PrescriptionItem, PrescriptionItemAdmin)

