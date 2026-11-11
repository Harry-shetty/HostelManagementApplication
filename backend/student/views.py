from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash

from housing.models import (
    Hostel, Student, Room, Bed, Application, ApplicationPreference,
    RoommateProfile, RoommateSuggestion, Notification, UserProfile
)
from housing.decorators import student_required
from housing.views import get_base_context

@student_required
def overview(request):
    ctx = get_base_context(request, 'overview', is_admin=False)
    ctx.update({
        'hostels': Hostel.objects.all()[:2],
        'application': Application.objects.first(),
        'notifications': Notification.objects.all()[:3],
    })
    return render(request, 'student/overview.html', ctx)

@student_required
def hostels_view(request):
    query = request.GET.get('q', '').strip()
    hostels_qs = Hostel.objects.all()
    if query:
        hostels_qs = hostels_qs.filter(name__icontains=query)

    ctx = get_base_context(request, 'hostels', is_admin=False)
    ctx.update({
        'hostels': hostels_qs,
        'search_query': query,
        'total_available': sum(h.beds_available for h in hostels_qs),
    })
    return render(request, 'student/hostels.html', ctx)

@student_required
def roommate_view(request):
    student = Student.objects.filter(student_id='STU-204810').first()
    matches = RoommateSuggestion.objects.filter(target_student=student) if student else []

    ctx = get_base_context(request, 'roommate', is_admin=False)
    ctx.update({
        'matches': matches,
        'student': student,
    })
    return render(request, 'student/roommate.html', ctx)

@student_required
def application_view(request):
    student = Student.objects.filter(student_id='STU-204810').first()
    app = Application.objects.filter(student=student).first() if student else None
    preferences = app.preferences.all().select_related('hostel') if app else []

    ctx = get_base_context(request, 'application', is_admin=False)
    ctx.update({
        'student': student,
        'application': app,
        'preferences': preferences,
        'hostels': Hostel.objects.all(),
    })
    return render(request, 'student/application.html', ctx)

@student_required
def status_view(request):
    student = Student.objects.filter(student_id='STU-204810').first()
    app = Application.objects.filter(student=student).first() if student else None

    ctx = get_base_context(request, 'status', is_admin=False)
    ctx.update({
        'student': student,
        'application': app,
    })
    return render(request, 'student/status.html', ctx)

@student_required
def placeholder_view(request, section):
    profile = getattr(request.user, 'profile', None)
    is_admin = request.user.is_staff or (profile and profile.is_admin())
    ctx = get_base_context(request, section, is_admin=is_admin)
    ctx.update({
        'section_name': section.replace('-', ' ').title(),
    })
    return render(request, 'student/placeholder.html', ctx)

@student_required
def profile_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()
    
    success_msg = None
    error_msg = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        programme = request.POST.get('programme', '').strip()
        year = request.POST.get('year', '').strip()
        emergency_contact = request.POST.get('emergency_contact', '').strip()
        bio = request.POST.get('bio', '').strip()
        
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if new_password:
            if not current_password:
                error_msg = 'Please enter your current password to set a new password.'
            elif not request.user.check_password(current_password):
                error_msg = 'Current password does not match our records.'
            elif len(new_password) < 6:
                error_msg = 'New password must be at least 6 characters long.'
            elif new_password != confirm_password:
                error_msg = 'New password and confirmation do not match.'
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)

        if not error_msg:
            if student:
                if name:
                    student.name = name
                    parts = name.split()
                    request.user.first_name = parts[0]
                    request.user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                if email:
                    student.email = email
                    request.user.email = email
                if phone:
                    student.phone = phone
                if programme:
                    student.programme = programme
                if year:
                    student.year = year
                if emergency_contact:
                    student.emergency_contact = emergency_contact
                if bio is not None:
                    student.bio = bio
                student.save()
                request.user.save()
            success_msg = 'Your profile details have been successfully updated!'

    ctx = get_base_context(request, 'student-profile', is_admin=False)
    ctx.update({
        'student': student,
        'success_msg': success_msg,
        'error_msg': error_msg,
    })
    return render(request, 'student/profile.html', ctx)

# ==================== AJAX APIs ====================

def api_hostels(request):
    q = request.GET.get('q', '').lower()
    hostels = Hostel.objects.all()
    data = []
    for h in hostels:
        if q and q not in h.name.lower() and q not in h.location.lower():
            continue
        data.append({
            'name': h.name,
            'loc': h.location,
            'beds': h.beds_available,
            'price': h.price_per_semester,
            'img': h.image_url,
            'room': h.room_summary,
            'tags': h.tags,
        })
    return JsonResponse({'hostels': data})

@require_POST
def api_toggle_save_match(request, match_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    match = get_object_or_404(RoommateSuggestion, id=match_id)
    match.is_saved = not match.is_saved
    match.save()
    return JsonResponse({'success': True, 'is_saved': match.is_saved})
