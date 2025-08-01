from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.gym_dashboard, name='gym_dashboard'),
    
    # Members
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.add_member, name='add_member'),
    path('members/<int:member_id>/', views.member_detail, name='member_detail'),
    path('members/<int:member_id>/renew/', views.renew_membership, name='renew_membership'),
    path('members/<int:member_id>/notify/', views.send_member_notification, name='send_member_notification'),
    
    # Attendance
    path('attendance/', views.record_attendance, name='record_attendance'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    
    # Visitors
    path('visitors/', views.visitor_list, name='visitor_list'),
    path('visitors/add/', views.add_visitor, name='add_visitor'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    
    # Financial Reports
    path('reports/', views.financial_reports, name='financial_reports'),
    
    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.create_staff, name='create_staff'),
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    
    # Registration Link
    path('share-link/', views.share_registration_link, name='share_registration_link'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Plans
    path('plans/', views.manage_plans, name='manage_plans'),
    
]