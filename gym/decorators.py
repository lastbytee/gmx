from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Gym

def gym_owner_or_staff_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            gym_id = kwargs.get('gym_id')
            if not gym_id:
                # Try to get gym from member, etc.
                if 'member_id' in kwargs:
                    from .models import Member
                    member = get_object_or_404(Member, pk=kwargs['member_id'])
                    gym_id = member.gym.id
                # Add other cases as needed

            if not gym_id:
                 raise PermissionDenied("Gym not found.")

            gym = get_object_or_404(Gym, pk=gym_id)
            user = request.user

            if user.is_authenticated:
                if user.role == 'gym_owner' and gym.owner == user:
                    return view_func(request, *args, **kwargs)

                if user.role == 'staff' and hasattr(user, 'staff') and user.staff.gym == gym:
                    if permission is None or getattr(user.staff, permission, False):
                        return view_func(request, *args, **kwargs)

            raise PermissionDenied
        return _wrapped_view
    return decorator
