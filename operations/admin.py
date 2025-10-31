from django.contrib import admin
from .models import Operation, OperationMedia


class OperationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'operation_name')
    search_fields = ('operation_name', 'operation_date')
    list_filter = ('status', )


class OperationMediaAdmin(admin.ModelAdmin):
    list_display = ('operation', 'media_type', 'created_at')
    list_filter = ('media_type', )


admin.site.register(Operation, OperationAdmin)
admin.site.register(OperationMedia, OperationMediaAdmin)

