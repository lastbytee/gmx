from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, date
from django.core.paginator import Paginator
from core.forms import ExpenseForm, GymForm, GymPlanForm, InvoiceForm, MemberForm, StaffForm, VisitorForm
from .models import Attendance, Expense, Gym, Invoice, Member, Staff, Visitor
from core.models import Notification, PaymentMethod
from .decorators import gym_owner_or_staff_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

@login_required
def gym_dashboard(request):
    gyms = request.user.gyms.all()  # Using related_name 'gyms' from your model

    today = timezone.now().date()

    gyms_data = []
    for gym in gyms:
        members = gym.members.all()
        active_members = members.filter(is_active=True)
        expiring_members = members.filter(expiry_date__range=(today, today + timedelta(days=7)))
        expired_members = members.filter(expiry_date__lt=today, is_active=True)

        attendance = gym.attendance_set.filter(timestamp__date=today)
        member_attendance = attendance.filter(attendance_type='member').count()
        staff_attendance = attendance.filter(attendance_type='staff').count()

        income = gym.invoices.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
        expenses = gym.expenses.aggregate(total=Sum('amount'))['total'] or 0
        net_profit = income - expenses

        recent_members = members.order_by('-registration_date')[:5]
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]

        gyms_data.append({
            'gym': gym,
            'active_members_count': active_members.count(),
            'expiring_members_count': expiring_members.count(),
            'expired_members_count': expired_members.count(),
            'member_attendance': member_attendance,
            'staff_attendance': staff_attendance,
            'income': income,
            'expenses': expenses,
            'net_profit': net_profit,
            'recent_members': recent_members,
            'notifications': notifications,
        })

    context = {
        'gyms_data': gyms_data,
    }
    return render(request, 'gym/dashboard.html', context)


@login_required
def member_list(request):
    gym = get_object_or_404(Gym, owner=request.user)
    status = request.GET.get('status', 'active')
    search_query = request.GET.get('search', '')
    
    members = gym.members.all()
    
    # Apply status filter
    today = date.today()
    if status == 'active':
        members = members.filter(is_active=True)
    elif status == 'expiring':
        members = members.filter(expiry_date__range=(today, today + timedelta(days=7)))
    elif status == 'expired':
        members = members.filter(expiry_date__lt=today, is_active=True)
    
    # Apply search
    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'search_query': search_query,
        'gym': gym
    }
    return render(request, 'gym/member_list.html', context)

@login_required
def member_detail(request, member_id):
    member = get_object_or_404(Member, id=member_id, gym__owner=request.user)
    attendance = Attendance.objects.filter(member=member).order_by('-timestamp')[:10]
    
    context = {
        'member': member,
        'attendance': attendance
    }
    return render(request, 'gym/member_detail.html', context)

@login_required
def attendance_report(request):
    gym = get_object_or_404(Gym, owner=request.user)
    date_from = request.GET.get('from', date.today() - timedelta(days=7))
    date_to = request.GET.get('to', date.today())
    
    # Convert to date objects if strings
    if isinstance(date_from, str):
        date_from = date.fromisoformat(date_from)
    if isinstance(date_to, str):
        date_to = date.fromisoformat(date_to)
    
    attendance = Attendance.objects.filter(
        gym=gym,
        timestamp__date__range=[date_from, date_to]
    )
    
    # Group by date
    attendance_by_date = {}
    current_date = date_from
    while current_date <= date_to:
        day_attendance = attendance.filter(timestamp__date=current_date)
        member_count = day_attendance.filter(attendance_type='member').count()
        staff_count = day_attendance.filter(attendance_type='staff').count()
        attendance_by_date[current_date] = {
            'member': member_count,
            'staff': staff_count,
            'total': member_count + staff_count
        }
        current_date += timedelta(days=1)
    
    context = {
        'gym': gym,
        'date_from': date_from,
        'date_to': date_to,
        'attendance_by_date': attendance_by_date
    }
    return render(request, 'gym/attendance_report.html', context)

@login_required
@gym_owner_or_staff_required('can_manage_finances')
def invoice_list(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    invoices = gym.invoices.all().order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(description__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )
    
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'gym': gym
    }
    return render(request, 'gym/invoice_list.html', context)

@login_required
@gym_owner_or_staff_required('can_manage_finances')
def create_invoice(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.gym = gym
            invoice.save()
            messages.success(request, 'Invoice created successfully!')
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/create_invoice.html', context)

@login_required
@gym_owner_or_staff_required('can_manage_finances')
def visitor_list(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    visitors = Visitor.objects.filter(gym=gym).order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        visitors = visitors.filter(name__icontains=search_query)
    
    paginator = Paginator(visitors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'gym': gym
    }
    return render(request, 'gym/visitor_list.html', context)

@login_required
@gym_owner_or_staff_required('can_manage_finances')
def expense_list(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    expenses = Expense.objects.filter(gym=gym).order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        expenses = expenses.filter(description__icontains=search_query)
    
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'gym': gym
    }
    return render(request, 'gym/expense_list.html', context)

@login_required
@gym_owner_or_staff_required('can_manage_finances')
def financial_reports(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    
    # Date range filtering
    date_from = request.GET.get('from', date.today().replace(day=1))
    date_to = request.GET.get('to', date.today())
    
    # Convert to date objects if strings
    if isinstance(date_from, str):
        date_from = date.fromisoformat(date_from)
    if isinstance(date_to, str):
        date_to = date.fromisoformat(date_to)
    
    # Calculate income
    member_income = gym.members.filter(
        registration_date__range=[date_from, date_to]
    ).aggregate(total=Sum('plan__price'))['total'] or 0
    
    visitor_income = Visitor.objects.filter(
        gym=gym,
        date__date__range=[date_from, date_to]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_income = member_income + visitor_income
    
    # Calculate expenses
    expenses = Expense.objects.filter(
        gym=gym,
        date__range=[date_from, date_to]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Net profit
    net_profit = total_income - expenses
    
    # Income sources
    income_sources = {
        'Memberships': member_income,
        'Visitors': visitor_income
    }
    
    context = {
        'gym': gym,
        'date_from': date_from,
        'date_to': date_to,
        'member_income': member_income,
        'visitor_income': visitor_income,
        'total_income': total_income,
        'expenses': expenses,
        'net_profit': net_profit,
        'income_sources': income_sources,
    }
    return render(request, 'gym/financial_reports.html', context)

@login_required
def share_registration_link(request):
    gym = get_object_or_404(Gym, owner=request.user)
    registration_link = f"{request.scheme}://{request.get_host()}/gym/register/{gym.id}/"
    
    context = {
        'gym': gym,
        'registration_link': registration_link
    }
    return render(request, 'gym/share_registration_link.html', context)

@login_required
def staff_list(request):
    gym = get_object_or_404(Gym, owner=request.user)
    staff = gym.staff.all()
    
    context = {
        'staff': staff,
        'gym': gym
    }
    return render(request, 'gym/staff_list.html', context)

@login_required
def create_staff(request):
    gym = get_object_or_404(Gym, owner=request.user)
    
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.gym = gym
            staff.save()
            messages.success(request, 'Staff member added successfully!')
            return redirect('staff_list')
    else:
        form = StaffForm()
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/create_staff.html', context)

@login_required
def notifications(request):
    gym = get_object_or_404(Gym, owner=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    if request.method == 'POST':
        notifications.update(is_read=True)
        return redirect('notifications')
    
    context = {
        'notifications': notifications,
        'gym': gym
    }
    return render(request, 'gym/notifications.html', context)

@login_required
def send_member_notification(request, member_id):
    member = get_object_or_404(Member, id=member_id, gym__owner=request.user)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            Notification.objects.create(
                user=request.user,  # Store in gym owner's notifications
                message=f"Notification sent to {member.name}: {message}",
                link=f"/gym/members/{member.id}/"
            )
            # In a real app, you would send this to the member (email/SMS)
            messages.success(request, 'Notification sent successfully!')
            return redirect('member_detail', member_id=member.id)
    
    context = {
        'member': member
    }
    return render(request, 'gym/send_member_notification.html', context)


@login_required
@gym_owner_or_staff_required('can_register_members')
def add_member(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    if not gym:
        return redirect('gym_dashboard')
    
    # Check member limit
    current_members = gym.members.count()
    if current_members >= gym.system_plan.member_limit:
        messages.error(request, 'You have reached your member limit. Please upgrade your plan.')
        return redirect('member_list')
    
    if request.method == 'POST':
        form = MemberForm(request.POST, gym=gym)
        if form.is_valid():
            member = form.save(commit=False)
            member.gym = gym
            member.save()
            messages.success(request, 'Member added successfully!')
            return redirect('member_detail', member_id=member.id)
    else:
        form = MemberForm(gym=gym)
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/add_member.html', context)

from django.conf import settings

# Renew Membership
def renew_membership(request, member_id):
    member = get_object_or_404(Member, id=member_id, gym__owner=request.user)
    
    if request.method == 'POST':
        # This part will be handled by Stripe's webhook or client-side confirmation
        # For now, we assume payment is successful and update the models
        member.is_active = True
        if 'duration' in member.plan.plan_type:
            member.expiry_date = timezone.now().date() + timedelta(days=member.plan.duration_days)
        elif 'session' in member.plan.plan_type:
            member.sessions_remaining = member.plan.session_count
        member.save()
        
        invoice = Invoice.objects.get(id=request.POST.get('invoice_id'))
        invoice.is_paid = True
        invoice.save()
        
        messages.success(request, 'Membership renewed successfully!')
        return redirect('member_detail', member_id=member.id)
    
    # Create a new invoice for the renewal
    invoice = Invoice.objects.create(
        gym=member.gym,
        amount=member.plan.price,
        payment_method=PaymentMethod.objects.get(name='card'), # Assume card payment
        description=f"Renewal for {member.name}",
        is_paid=False
    )

    context = {
        'member': member,
        'invoice': invoice,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    }
    return render(request, 'gym/renew_payment.html', context)

# Record Attendance
@login_required
@gym_owner_or_staff_required('can_manage_attendance')
def record_attendance(request):
    if request.user.role == 'gym_owner':
        gym = get_object_or_404(Gym, owner=request.user)
    else:
        gym = request.user.staff.gym
    if not gym:
        return redirect('gym_dashboard')
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        staff_id = request.POST.get('staff_id')
        
        if member_id:
            member = get_object_or_404(Member, id=member_id, gym=gym)
            Attendance.objects.create(
                gym=gym,
                attendance_type='member',
                member=member,
                method='manual'
            )
            messages.success(request, f'Attendance recorded for {member.name}')
        elif staff_id:
            staff = get_object_or_404(Staff, id=staff_id, gym=gym)
            Attendance.objects.create(
                gym=gym,
                attendance_type='staff',
                staff=staff,
                method='manual'
            )
            messages.success(request, f'Attendance recorded for {staff.user.username}')
        
        return redirect('record_attendance')
    
    members = gym.members.filter(is_active=True)
    staff = gym.staff.filter(is_active=True)
    
    context = {
        'members': members,
        'staff': staff,
        'gym': gym
    }
    return render(request, 'gym/record_attendance.html', context)

# Invoice Detail
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, gym__owner=request.user)
    context = {
        'invoice': invoice
    }
    return render(request, 'gym/invoice_detail.html', context)

# Add Visitor
def add_visitor(request):
    gym = request.user.gym_set.first()
    if not gym:
        return redirect('gym_dashboard')
    
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.gym = gym

            # Create an invoice for the visitor
            invoice = Invoice.objects.create(
                gym=gym,
                amount=visitor.amount,
                payment_method=visitor.payment_method,
                description=f"Visitor pass for {visitor.name}",
                is_paid=False
            )

            # If payment is by card, redirect to payment page
            if visitor.payment_method.name == 'card':
                context = {
                    'visitor': visitor,
                    'invoice': invoice,
                    'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
                }
                return render(request, 'gym/visitor_payment.html', context)
            else:
                # For cash or other methods, mark as paid and save
                invoice.is_paid = True
                invoice.save()
                visitor.save()
                messages.success(request, 'Visitor recorded successfully!')
                return redirect('visitor_list')
    else:
        form = VisitorForm()
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/add_visitor.html', context)

# Add Expense
def add_expense(request):
    gym = request.user.gym_set.first()
    if not gym:
        return redirect('gym_dashboard')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.gym = gym
            expense.save()
            messages.success(request, 'Expense recorded successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/add_expense.html', context)

# Staff Detail
def staff_detail(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id, gym__owner=request.user)
    attendance = Attendance.objects.filter(staff=staff).order_by('-timestamp')[:10]
    
    context = {
        'staff': staff,
        'attendance': attendance
    }
    return render(request, 'gym/staff_detail.html', context)

# Manage Plans
def manage_plans(request):
    gym = request.user.gym_set.first()
    if not gym:
        return redirect('gym_dashboard')
    
    plans = gym.plans.all()
    
    if request.method == 'POST':
        form = GymPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.gym = gym
            plan.save()
            messages.success(request, 'Plan created successfully!')
            return redirect('manage_plans')
    else:
        form = GymPlanForm()
    
    context = {
        'plans': plans,
        'form': form,
        'gym': gym
    }
    return render(request, 'gym/manage_plans.html', context)

@login_required
def staff_dashboard(request):
    staff = get_object_or_404(Staff, user=request.user)
    gym = staff.gym

    context = {
        'staff': staff,
        'gym': gym
    }
    return render(request, 'gym/staff_dashboard.html', context)
