from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Attendance,  Gym, Member, PaymentMethod, Invoice, Notification, Staff, SystemPlan
from .forms import ExpenseForm, GymPlanForm, UserRegisterForm, UserLoginForm, GymForm, MemberForm, VisitorForm

def home(request):
    plans = SystemPlan.objects.all()
    context = {
        'plans': plans
    }
    return render(request, 'home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            # Handle role-specific redirection
            if user.role == 'system_admin':
                login(request, user)
                return redirect('system_dashboard')
            else:
                login(request, user)
                return redirect('gym_register')
    else:
        form = UserRegisterForm()
    return render(request, 'auth/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard_redirect')
        messages.error(request, "Invalid credentials")
    else:
        form = UserLoginForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_redirect(request):
    if request.user.role == 'system_admin':
        return redirect('system_dashboard')
    elif request.user.role == 'gym_owner':
        return redirect('gym_dashboard')
    return redirect('home')

PENDING_PAYMENT_METHOD = 'pending'  # 🔒 Constant for safety

@login_required
def gym_register(request):
    if request.user.role != 'gym_owner':
        return redirect('home')
    
    if request.method == 'POST':
        form = GymForm(request.POST, user=request.user)
        if form.is_valid():
            gym = form.save(commit=False)
            gym.owner = request.user
            gym.save()

            # ✅ Ensure the 'pending' payment method exists
            payment_method, _ = PaymentMethod.objects.get_or_create(
                name=PENDING_PAYMENT_METHOD,
                defaults={'is_active': False}
            )

            # ✅ Create initial invoice
            Invoice.objects.create(
                gym=gym,
                amount=gym.system_plan.price,
                payment_method=payment_method,
                description=f"Initial subscription for {gym.name}"
            )
            
            messages.success(request, 'Gym registered successfully! Please complete payment.')
            return redirect('gym_payment', gym_id=gym.id)
    else:
        form = GymForm(user=request.user)
    
    return render(request, 'gym/gym_register.html', {'form': form})


@login_required
def gym_payment(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    invoice = gym.invoices.first()
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)

        invoice.payment_method = payment_method
        
        if payment_method.name.lower() in ['momo', 'card']:
            # ✅ Simulate instant payment confirmation
            invoice.is_paid = True
            gym.is_active = True
            gym.is_approved = True
            gym.save()
            messages.success(request, 'Payment successful! Your gym is now active.')
        else:
            # 🕐 Cash or delayed payment
            invoice.is_paid = False
            messages.info(request, 'Your payment is pending approval. You will be notified once approved.')
        
        invoice.save()
        return redirect('gym_dashboard')
    
    context = {
        'gym': gym,
        'invoice': invoice,
        'payment_methods': payment_methods
    }
    return render(request, 'gym/payment.html', context)

@login_required
def scan_qr_attendance(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        qr_data = request.POST.get('qr_data')
        gym_id = request.POST.get('gym_id')
        
        try:
            # In a real implementation, you would decrypt and verify the QR data
            # For simplicity, we're using a dummy implementation
            member_id = qr_data.split('_')[-1]  # Extract member ID
            member = Member.objects.get(id=member_id, gym_id=gym_id)
            
            # Check if member is active
            if not member.is_active:
                return JsonResponse({'status': 'error', 'message': 'Membership expired'})
            
            # Record attendance
            Attendance.objects.create(
                gym=member.gym,
                attendance_type='member',
                member=member,
                method='qr'
            )
            return JsonResponse({'status': 'success', 'member_name': member.name})
        except Member.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid QR code'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def register_member(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    
    # Check member limit
    current_members = gym.members.count()
    if current_members >= gym.system_plan.member_limit:
        messages.error(request, 'You have reached your member limit. Please upgrade your plan.')
        return redirect('gym_dashboard')
    
    if request.method == 'POST':
        form = MemberForm(request.POST, gym=gym)
        if form.is_valid():
            member = form.save(commit=False)
            member.gym = gym
            member.save()
            
            # Create invoice for membership
            Invoice.objects.create(
                gym=gym,
                amount=member.plan.price,
                payment_method=PaymentMethod.objects.get(name='cash'),
                description=f"Membership for {member.name}",
                is_paid=True
            )
            
            messages.success(request, 'Member registered successfully!')
            return redirect('member_detail', member_id=member.id)
    else:
        form = MemberForm(gym=gym)
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/register_member.html', context)

@login_required
def user_profile(request):
    user = request.user
    gym = None
    
    if user.role == 'gym_owner':
        gym = Gym.objects.filter(owner=user).first()
    
    context = {
        'user': user,
        'gym': gym
    }
    return render(request, 'profile.html', context)

@login_required
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': notifications
    }
    return render(request, 'notifications.html', context)

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read')
    return redirect('user_notifications')

@login_required
def process_payment(request):
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        payment_method_id = request.POST.get('payment_method_id')
        
        invoice = get_object_or_404(Invoice, id=invoice_id)
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
        
        invoice.payment_method = payment_method
        invoice.is_paid = True
        invoice.save()
        
        # Handle gym activation if it's a registration payment
        if invoice.description.startswith('Initial subscription'):
            invoice.gym.is_active = True
            invoice.gym.is_approved = True
            invoice.gym.save()
            
            # Send notification to gym owner
            Notification.objects.create(
                user=invoice.gym.owner,
                message=f"Your payment for {invoice.gym.name} has been processed! Your gym is now active.",
                link="/gym/dashboard/"
            )
        
        messages.success(request, 'Payment processed successfully!')
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    return redirect('home')
