from django.contrib import admin
from .models import Salary, Advance


class SalaryAdmin(admin.ModelAdmin):
    list_display = ('receptionist', 'base_salary', 'salary_month')
    search_fields = ('created_at', )
    list_filter = ('status', )


class AdvanceAdmin(admin.ModelAdmin):
    list_display = ('receptionist', 'amount', 'status', 'approved_by')
    list_filter = ('status', )


admin.site.register(Salary, SalaryAdmin)
admin.site.register(Advance, AdvanceAdmin)

