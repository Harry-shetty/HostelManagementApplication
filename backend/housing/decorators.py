from functools import wraps
from django.shortcuts import redirect, render
from django.urls import reverse

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        
        profile = getattr(request.user, 'profile', None)
        is_admin = request.user.is_staff or request.user.is_superuser or (profile and profile.is_admin())
        
        if not is_admin:
            return render(request, 'housing/access_denied.html', {
                'required_role': 'Warden Admin',
                'current_user': request.user,
            }, status=403)
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

