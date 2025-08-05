from django.contrib import admin
from .models import SystemPlan, SystemSetting

class SystemPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'duration_days', 'gym_limit', 'member_limit')
    list_filter = ('plan_type',)
    search_fields = ('name',)

admin.site.register(SystemPlan, SystemPlanAdmin)
admin.site.register(SystemSetting)
