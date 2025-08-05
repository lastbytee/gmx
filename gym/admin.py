from django.contrib import admin
from .models import Gym, GymPlan, Member, Visitor, Attendance, Staff, Invoice, Expense

class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'system_plan', 'registration_date', 'expiry_date', 'is_active', 'is_approved')
    list_filter = ('is_active', 'is_approved', 'system_plan')
    search_fields = ('name', 'owner__username', 'email')
    raw_id_fields = ('owner',)
    readonly_fields = ('registration_date',)

class GymPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'gym', 'plan_type', 'price', 'duration_days', 'session_count')
    list_filter = ('plan_type', 'gym')
    search_fields = ('name', 'gym__name')
    raw_id_fields = ('gym',)

class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'gym', 'member_type', 'plan', 'registration_date', 'expiry_date', 'is_active')
    list_filter = ('member_type', 'is_active', 'gym', 'gender')
    search_fields = ('name', 'phone', 'email', 'gym__name')
    raw_id_fields = ('gym', 'plan')
    readonly_fields = ('registration_date', 'qr_code')
    list_select_related = ('gym', 'plan')

class VisitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'gym', 'amount', 'payment_method', 'date')
    list_filter = ('payment_method', 'gym')
    search_fields = ('name', 'gym__name')
    raw_id_fields = ('gym',)
    date_hierarchy = 'date'

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('gym', 'attendance_type', 'member', 'staff', 'timestamp', 'method')
    list_filter = ('attendance_type', 'method', 'gym')
    search_fields = ('member__name', 'staff__user__username', 'gym__name')
    raw_id_fields = ('gym', 'member', 'staff')
    date_hierarchy = 'timestamp'

class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'gym', 'position', 'is_active')
    list_filter = ('is_active', 'gym', 'position')
    search_fields = ('user__username', 'gym__name', 'position')
    raw_id_fields = ('user', 'gym')

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('gym', 'amount', 'payment_method', 'date', 'is_paid')
    list_filter = ('is_paid', 'payment_method', 'gym')
    search_fields = ('gym__name', 'description', 'transaction_id')
    raw_id_fields = ('gym',)
    date_hierarchy = 'date'
    readonly_fields = ('date',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'gym', 'amount', 'date', 'category')
    list_filter = ('category', 'gym')
    search_fields = ('description', 'gym__name', 'category')
    raw_id_fields = ('gym',)
    date_hierarchy = 'date'

admin.site.register(Gym, GymAdmin)
admin.site.register(GymPlan, GymPlanAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Visitor, VisitorAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Expense, ExpenseAdmin)
