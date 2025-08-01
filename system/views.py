import base64
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from django.core.paginator import Paginator
import qrcode
from core.forms import GymForm, SystemPlanForm, SystemSettingsForm
from core.models import Gym, Invoice, Expense, Notification, SystemPlan, SystemSetting, User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail

@login_required
def system_dashboard(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    today = timezone.now().date()
    
    # Gym statistics
    gyms = Gym.objects.all()
    active_gyms = gyms.filter(is_active=True)
    expiring_gyms = gyms.filter(expiry_date__range=(today, today + timedelta(days=30)))
    expired_gyms = gyms.filter(expiry_date__lt=today, is_active=True)
    
    # Financial statistics
    total_income = Invoice.objects.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.filter(gym__isnull=True).aggregate(total=Sum('amount'))['total'] or 0
    net_profit = total_income - total_expenses
    
    # Recent activities
    recent_gyms = gyms.order_by('-registration_date')[:5]
    recent_invoices = Invoice.objects.filter(is_paid=True).order_by('-date')[:5]
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'active_gyms_count': active_gyms.count(),
        'expiring_gyms_count': expiring_gyms.count(),
        'expired_gyms_count': expired_gyms.count(),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'recent_gyms': recent_gyms,
        'recent_invoices': recent_invoices,
        'notifications': notifications,
    }
    return render(request, 'system/dashboard.html', context)

@login_required
def gym_list(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    status = request.GET.get('status', 'active')
    search_query = request.GET.get('search', '')
    
    gyms = Gym.objects.all()
    
    # Apply status filter
    today = date.today()
    if status == 'active':
        gyms = gyms.filter(is_active=True)
    elif status == 'expiring':
        gyms = gyms.filter(expiry_date__range=(today, today + timedelta(days=30)))
    elif status == 'expired':
        gyms = gyms.filter(expiry_date__lt=today, is_active=True)
    
    # Apply search
    if search_query:
        gyms = gyms.filter(
            Q(name__icontains=search_query) |
            Q(owner__username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    paginator = Paginator(gyms, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'search_query': search_query
    }
    return render(request, 'system/gym_list.html', context)

@login_required
def gym_detail(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    members = gym.members.all()
    invoices = gym.invoices.all().order_by('-date')[:5]
    
    # Calculate days until expiration
    days_until_expiry = (gym.expiry_date - date.today()).days
    
    context = {
        'gym': gym,
        'members_count': members.count(),
        'invoices': invoices,
        'days_until_expiry': days_until_expiry
    }
    return render(request, 'system/gym_detail.html', context)

@login_required
def approve_gym(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    
    if request.method == 'POST':
        gym.is_approved = True
        gym.is_active = True
        gym.save()
        
        # Create notification for gym owner
        Notification.objects.create(
            user=gym.owner,
            message=f"Your gym {gym.name} has been approved!",
            link="/gym/dashboard/"
        )
        
        messages.success(request, 'Gym approved successfully!')
        return redirect('gym_detail', gym_id=gym.id)
    
    return render(request, 'system/approve_gym.html', {'gym': gym})

@login_required
def income_report(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    # Date range filtering
    date_from = request.GET.get('from', date.today().replace(day=1))
    date_to = request.GET.get('to', date.today())
    
    # Convert to date objects if strings
    if isinstance(date_from, str):
        date_from = date.fromisoformat(date_from)
    if isinstance(date_to, str):
        date_to = date.fromisoformat(date_to)
    
    # Aggregate income by gym
    gym_income = Gym.objects.annotate(
        total_income=Sum('invoices__amount', filter=Q(invoices__is_paid=True, invoices__date__range=[date_from, date_to]))
    ).exclude(total_income=None)
    
    total_income = sum(gym.total_income for gym in gym_income if gym.total_income)
    
    # Income sources
    sources = {
        'subscriptions': total_income,
        'renewals': 0  # In a real app, you'd calculate this
    }
    
    context = {
        'gym_income': gym_income,
        'total_income': total_income,
        'sources': sources,
        'date_from': date_from,
        'date_to': date_to
    }
    return render(request, 'system/income_report.html', context)

@login_required
def invoice_list(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    invoices = Invoice.objects.filter(is_paid=True).order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(gym__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query
    }
    return render(request, 'system/invoice_list.html', context)

@login_required
def expense_list(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    expenses = Expense.objects.filter(gym__isnull=True).order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        expenses = expenses.filter(description__icontains=search_query)
    
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query
    }
    return render(request, 'system/expense_list.html', context)

@login_required
def financial_report(request):
    if request.user.role != 'system_admin':
        return redirect('home')
    
    # Date range filtering
    date_from = request.GET.get('from', date.today().replace(day=1))
    date_to = request.GET.get('to', date.today())
    
    # Convert to date objects if strings
    if isinstance(date_from, str):
        date_from = date.fromisoformat(date_from)
    if isinstance(date_to, str):
        date_to = date.fromisoformat(date_to)
    
    # Calculate income
    income = Invoice.objects.filter(
        is_paid=True,
        date__range=[date_from, date_to]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate expenses
    expenses = Expense.objects.filter(
        gym__isnull=True,
        date__range=[date_from, date_to]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Net profit
    net_profit = income - expenses
    
    context = {
        'income': income,
        'expenses': expenses,
        'net_profit': net_profit,
        'date_from': date_from,
        'date_to': date_to
    }
    return render(request, 'system/financial_report.html', context)

@login_required
def renew_subscription(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    
    if request.method == 'POST':
        # Create renewal invoice
        Invoice.objects.create(
            gym=gym,
            amount=gym.system_plan.price,
            payment_method='pending',
            description=f"Renewal subscription for {gym.name}"
        )
        
        messages.success(request, 'Renewal invoice created. Gym owner can now complete payment.')
        return redirect('gym_detail', gym_id=gym.id)
    
    context = {
        'gym': gym,
        'plan': gym.system_plan
    }
    return render(request, 'system/renew_subscription.html', context)

def is_system_admin(user):
    return user.role == 'system_admin'

@login_required
@user_passes_test(is_system_admin)
def share_registration_link(request):
    registration_link = f"{request.scheme}://{request.get_host()}/register/"
    qr_img = qrcode.make(registration_link)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

    if request.method == 'POST':
        recipient_email = request.POST.get('email')
        custom_message = request.POST.get('message')

        if recipient_email:
            full_message = f"{custom_message}\n\nRegistration Link: {registration_link}"
            send_mail(
                subject='Gym Registration Invitation',
                message=full_message,
                from_email='your_email@example.com',  # Replace with your email or settings.DEFAULT_FROM_EMAIL
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            messages.success(request, f"Invitation sent to {recipient_email}!")
            return redirect('share_registration_link')
        else:
            messages.error(request, "Please provide a recipient email.")

    context = {
        'registration_link': registration_link,
        'qr_code_base64': qr_code_base64,
    }
    return render(request, 'system/share_registration_link.html', context)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    if request.method == 'POST':
        notifications.update(is_read=True)
        return redirect('notifications')
    
    context = {
        'notifications': notifications
    }
    return render(request, 'system/notifications.html', context)

@login_required
def send_notification(request):
    if request.method == 'POST':
        gym_id = request.POST.get('gym_id')
        message = request.POST.get('message')
        
        if gym_id == 'all':
            users = User.objects.filter(role='gym_owner')
            for user in users:
                Notification.objects.create(
                    user=user,
                    message=message,
                    link="/gym/dashboard/"
                )
        else:
            gym = get_object_or_404(Gym, id=gym_id)
            Notification.objects.create(
                user=gym.owner,
                message=message,
                link="/gym/dashboard/"
            )
        
        messages.success(request, 'Notification sent successfully!')
        return redirect('send_notification')
    
    gyms = Gym.objects.all()
    context = {
        'gyms': gyms
    }
    return render(request, 'system/send_notification.html', context)


@login_required
def system_settings(request):
    if request.user.role != 'system_admin':
        return redirect('home')

    initial_data = {
        setting.key: setting.value
        for setting in SystemSetting.objects.all()
    }
    form = SystemSettingsForm(initial=initial_data)

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "System settings updated.")
            return redirect('system_settings')

    context = {
        'form': form
    }
    return render(request, 'system/settings.html', context)

def manage_plans(request):
    if request.user.role != 'system_admin':
        return redirect('system_dashboard')
    
    plans = SystemPlan.objects.all()
    
    if request.method == 'POST':
        form = SystemPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan created successfully!')
            return redirect('manage_plans')
    else:
        form = SystemPlanForm()
    
    context = {
        'plans': plans,
        'form': form
    }
    return render(request, 'system/manage_plans.html', context)

@login_required
def add_gym(request):
    if request.user.role != 'system_admin':
        return redirect('home')

    if request.method == 'POST':
        form = GymForm(request.POST, user=request.user)
        if form.is_valid():
            gym = form.save(commit=False)
            gym.owner = request.user  # or assign to another user if needed
            gym.is_active = True
            gym.is_approved = True
            gym.save()
            messages.success(request, 'Gym added successfully!')
            return redirect('gym_list')
    else:
        form = GymForm(user=request.user)

    return render(request, 'system/add_gym.html', {'form': form})