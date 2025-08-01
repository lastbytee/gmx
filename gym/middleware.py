from django.http import HttpResponseForbidden
from django.urls import reverse

class PlanEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for system admin and non-gym URLs
        if not request.path.startswith('/gym/') or request.user.role == 'system_admin':
            return None
        
        # Skip for logout and non-authenticated users
        if not request.user.is_authenticated or request.path == reverse('logout'):
            return None
        
        # Check if user is trying to add a member
        if request.path == reverse('gym:add_member'):
            try:
                gym = request.user.gym_set.first()
                if not gym or not gym.can_add_member():
                    return HttpResponseForbidden(
                        "Member limit reached. Please upgrade your plan to add more members."
                    )
            except AttributeError:
                return HttpResponseForbidden("Gym not found")
        
        return None