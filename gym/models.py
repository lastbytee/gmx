from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.core.files import File

class Gym(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gyms')
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    system_plan = models.ForeignKey('system.SystemPlan', on_delete=models.SET_NULL, null=True)
    registration_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and self.system_plan:  # New instance
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

    def __str__(self):
        return self.name

class Staff(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='staff')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    can_register_members = models.BooleanField(default=False)
    can_manage_attendance = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

class Attendance(models.Model):
    ATTENDANCE_TYPES = (
        ('member', 'Member'),
        ('staff', 'Staff'),
    )
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    attendance_type = models.CharField(max_length=10, choices=ATTENDANCE_TYPES)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=(
        ('qr', 'QR Code'),
        ('manual', 'Manual'),
    ))

    def __str__(self):
        return f"{self.member or self.staff} - {self.timestamp}"

class Invoice(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey('core.PaymentMethod', on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.gym.name}"

class Visitor(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='visitors')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey('core.PaymentMethod', on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

class Expense(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.description
