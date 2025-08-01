from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.system_dashboard, name='system_dashboard'),
    
    # Gym Management
    path('gyms/', views.gym_list, name='gym_list'),
    path('gyms/add/', views.add_gym, name='add_gym'),

    path('gyms/<int:gym_id>/', views.gym_detail, name='gym_detail'),
    path('gyms/<int:gym_id>/approve/', views.approve_gym, name='approve_gym'),
    path('gyms/<int:gym_id>/renew/', views.renew_subscription, name='renew_subscription'),
    
    # Plans
    path('plans/', views.manage_plans, name='manage_plans'),

    
    # Financials
    path('income/', views.income_report, name='income_report'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('reports/', views.financial_report, name='report'),
    
    # Registration Link
    path('share-link/', views.share_registration_link, name='share_registration_link'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/send/', views.send_notification, name='send_notification'),
    
    # Settings
    path('settings/', views.system_settings, name='system_settings'),
]