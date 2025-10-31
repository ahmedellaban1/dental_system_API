from django.contrib import admin
from .models import CommonDisease, ChronicDisease


class CommonDiseaseAdmin(admin.ModelAdmin):
    list_display = ('disease_name_ar', 'disease_name_en', 'category')
    search_fields = ('disease_name_ar', 'disease_name_en', 'category')
    list_filter = ('category', )


class ChronicDiseaseAdmin(admin.ModelAdmin):
    list_display = ('patient', 'disease', 'description', 'diagnosed_date', 'is_active',)
    list_filter = ('is_active', )


admin.site.register(CommonDisease, CommonDiseaseAdmin)
admin.site.register(ChronicDisease, ChronicDiseaseAdmin)

