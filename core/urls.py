from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard redirect
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Gym registration flow
    path('gym/register/', views.gym_register, name='gym_register'),
    path('gym/payment/<int:gym_id>/', views.gym_payment, name='gym_payment'),
    
    # QR Code attendance
    path('scan-qr/', views.scan_qr_attendance, name='scan_qr_attendance'),
    
    # Member registration (for gym owners)
    path('gym/register-member/<int:gym_id>/', views.register_member, name='register_member'),
    
    # Shared views
    path('profile/', views.user_profile, name='user_profile'),
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Payment processing
    path('process-payment/', views.process_payment, name='process_payment'),
]