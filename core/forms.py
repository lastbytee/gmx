from django import forms
from django.contrib.auth.forms import UserCreationForm
import pytz
from .models import User, PaymentMethod, Notification
from gym.models import Invoice, Gym, GymPlan, Member, Visitor, Staff, Expense
from system.models import SystemSetting, SystemPlan

class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class SystemPlanForm(forms.ModelForm):
    class Meta:
        model = SystemPlan
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'gym_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'member_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GymForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = ['name', 'address', 'phone', 'email', 'system_plan']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'system_plan': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'gym_owner':
            self.fields['system_plan'].queryset = SystemPlan.objects.all()

class GymPlanForm(forms.ModelForm):
    class Meta:
        model = GymPlan
        fields = ['name', 'plan_type', 'price', 'duration_days', 'session_count', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'session_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name', 'email', 'phone', 'gender', 'member_type', 'plan']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'member_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        gym = kwargs.pop('gym', None)
        super().__init__(*args, **kwargs)
        if gym:
            self.fields['plan'].queryset = GymPlan.objects.filter(gym=gym)

class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['name', 'amount', 'payment_method']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['position', 'can_register_members', 'can_manage_attendance', 'can_manage_finances']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['message', 'link']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
        }

class InvoiceForm(forms.ModelForm):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Invoice
        fields = ['amount', 'payment_method', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.gym = kwargs.pop('gym', None)
        super().__init__(*args, **kwargs)
        if self.gym:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True)

    def save(self, commit=True):
        invoice = super().save(commit=False)
        if self.gym:
            invoice.gym = self.gym
        if commit:
            invoice.save()
        return invoice



# forms.py
class SystemSettingsForm(forms.Form):
    currency = forms.ChoiceField(
        choices=[('USD', 'USD'), ('EUR', 'EUR'), ('RWF', 'RWF')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.all_timezones],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    support_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    company_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    maintenance_mode = forms.BooleanField(required=False)

    def save(self):
        for field, value in self.cleaned_data.items():
            SystemSetting.objects.update_or_create(key=field, defaults={'value': value})
