from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

from .models import (
    Student, Notification, UserProfile
)

def get_base_context(request, active_view='overview', is_admin=False):
    notifications = Notification.objects.all()[:5]
    unread_count = notifications.count()
    
    current_user = request.user if request.user.is_authenticated else None
    profile = getattr(current_user, 'profile', None) if current_user else None
    user_is_admin = current_user and (current_user.is_staff or current_user.is_superuser or (profile and profile.is_admin()))

    student_obj = None
    if user_is_admin:
        full_name = f"{current_user.first_name} {current_user.last_name}".strip() if current_user else ''
        display_name = full_name if full_name else (profile.title if profile and profile.title else 'Dr. Sarah Moore')
        display_role = profile.title if (profile and profile.title) else 'Head Warden'
        clean_parts = [p for p in display_name.replace('Dr.', '').strip().split() if p]
        avatar = ''.join(p[0].upper() for p in clean_parts[:2]) if clean_parts else 'SM'
    else:
        student_obj = profile.student_profile if profile and profile.student_profile else Student.objects.filter(student_id='STU-204810').first()
        display_name = student_obj.name if student_obj else (current_user.username if current_user else 'Amara Mensah')
        display_role = f"{student_obj.programme} · {student_obj.year}" if student_obj else 'Student Portal'
        avatar = student_obj.avatar_initials if student_obj and student_obj.avatar_initials else 'AM'

    return {
        'active_view': active_view,
        'is_admin': is_admin,
        'user_is_admin': user_is_admin,
        'current_user': current_user,
        'profile': profile,
        'student_obj': student_obj,
        'unread_count': unread_count,
        'admin_name': display_name if user_is_admin else 'Dr. Sarah Moore',
        'admin_role': display_role if user_is_admin else 'Head Warden',
        'student_name': display_name if not user_is_admin else 'Amara Mensah',
        'student_meta': display_role if not user_is_admin else 'Computer Science · Year 2',
        'avatar': avatar,
    }

def login_view(request):
    next_url = request.GET.get('next', '')
    
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if request.user.is_staff or (profile and profile.is_admin()):
            return redirect(next_url or 'admin-overview')
        return redirect(next_url or 'overview')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_target = request.POST.get('next', '')

        # Support logging in with student_id
        student_user = Student.objects.filter(student_id=username).first()
        if student_user and hasattr(student_user, 'user_profile') and student_user.user_profile:
            username = student_user.user_profile.user.username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile = getattr(user, 'profile', None)
            is_admin = user.is_staff or user.is_superuser or (profile and profile.is_admin())
            
            if next_target:
                return redirect(next_target)
            return redirect('admin-overview' if is_admin else 'overview')
        else:
            error = 'Invalid credentials. Please verify your username and password.'

    return render(request, 'housing/login.html', {
        'error': error,
        'next_url': next_url,
    })

def logout_view(request):
    logout(request)
    return redirect('login')
