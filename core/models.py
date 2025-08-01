from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import uuid
import qrcode
from io import BytesIO
from django.core.files import File

class User(AbstractUser):
    ROLE_CHOICES = (
        ('gym_owner', 'Gym Owner'),
        ('system_admin', 'System Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class SystemPlan(models.Model):
    PLAN_TYPES = (
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
    )
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    gym_limit = models.PositiveIntegerField()
    member_limit = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.plan_type})"

class Gym(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gyms')
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    system_plan = models.ForeignKey(SystemPlan, on_delete=models.SET_NULL, null=True)
    registration_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            self.expiry_date = timezone.now().date() + timedelta(days=self.system_plan.duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class GymPlan(models.Model):
    PLAN_TYPES = (
        ('individual_duration', 'Individual Duration'),
        ('group_duration', 'Group Duration'),
        ('individual_session', 'Individual Session'),
        ('group_session', 'Group Session'),
    )
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    session_count = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.gym.name}"

class Member(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    MEMBER_TYPES = (
        ('individual', 'Individual'),
        ('group', 'Group'),
    )
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPES)
    plan = models.ForeignKey(GymPlan, on_delete=models.SET_NULL, null=True, blank=True)
    registration_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    sessions_remaining = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # New member
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            data = {
                'member_id': self.id,
                'gym_id': self.gym.id,
                'name': self.name,
                'plan': self.plan.name if self.plan else 'None'
            }
            qr.add_data(str(data))
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr_{self.id}.png'
            self.qr_code.save(file_name, File(buffer), save=False)
            
            # Set expiration if duration-based plan
            if self.plan and 'duration' in self.plan.plan_type:
                self.expiry_date = timezone.now().date() + timedelta(days=self.plan.duration_days)
            # Set session count if session-based plan
            if self.plan and 'session' in self.plan.plan_type:
                self.sessions_remaining = self.plan.session_count
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    ATTENDANCE_TYPES = (
        ('member', 'Member'),
        ('staff', 'Staff'),
    )
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    attendance_type = models.CharField(max_length=10, choices=ATTENDANCE_TYPES)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=(
        ('qr', 'QR Code'),
        ('manual', 'Manual'),
    ))

    def __str__(self):
        return f"{self.member or self.staff} - {self.timestamp}"
class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('momo', 'MTN MoMo'),
        ('card', 'Card'),
    )
    name = models.CharField(max_length=50, choices=METHOD_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()

# Update Invoice model to use PaymentMethod
class Invoice(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)  # For digital payments

    def __str__(self):
        return f"Invoice #{self.id} - {self.gym.name}"

class Visitor(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='visitors')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date}"
class Staff(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='staff')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    can_register_members = models.BooleanField(default=False)
    can_manage_attendance = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


class Expense(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.description

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
    

# models.py
class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
  