from django import template
from datetime import date, timedelta

from core.models import Gym

register = template.Library()

@register.simple_tag
def get_active_gym_count():
    return Gym.objects.filter(is_active=True).count()

@register.simple_tag
def get_expiring_gym_count():
    today = date.today()
    return Gym.objects.filter(expiry_date__range=(today, today + timedelta(days=7))).count()

@register.filter
def days_until(value):
    if not value:
        return ""
    delta = value - date.today()
    return delta.days