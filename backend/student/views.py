from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache

from housing.models import (
    Hostel, Student, Application,
    RoommateSuggestion, Notification,
    AllocationLetter, RoomChangeRequest, AllocationRun, AuditLog
)
from housing.decorators import student_required
from housing.views import get_base_context, invalidate_student_caches

@student_required
def overview(request):
    ctx = get_base_context(request, 'overview', is_admin=False)
    overview_data = cache.get('student_overview_data')
    if not overview_data:
        overview_data = {
            'hostels': list(Hostel.objects.all()[:2]),
            'application': Application.objects.first(),
            'notifications': list(Notification.objects.all()[:3]),
        }
        cache.set('student_overview_data', overview_data, 180)

    ctx.update(overview_data)
    return render(request, 'student/overview.html', ctx)

@student_required
def hostels_view(request):
    query = request.GET.get('q', '').strip()
    all_hostels = cache.get('all_hostels_list')
    if not all_hostels:
        all_hostels = list(Hostel.objects.all())
        cache.set('all_hostels_list', all_hostels, 300)

    if query:
        hostels_qs = [h for h in all_hostels if query.lower() in h.name.lower()]
    else:
        hostels_qs = all_hostels

    ctx = get_base_context(request, 'hostels', is_admin=False)
    ctx.update({
        'hostels': hostels_qs,
        'search_query': query,
        'total_available': sum(h.beds_available for h in hostels_qs),
    })
    return render(request, 'student/hostels.html', ctx)

@student_required
def roommate_view(request):
    roommate_data = cache.get('student_roommate_data')
    if not roommate_data:
        student = Student.objects.filter(student_id='STU-204810').first()
        matches = list(RoommateSuggestion.objects.filter(target_student=student).select_related('suggested_student', 'target_student')) if student else []
        roommate_data = {
            'matches': matches,
            'student': student,
        }
        cache.set('student_roommate_data', roommate_data, 180)

    ctx = get_base_context(request, 'roommate', is_admin=False)
    ctx.update(roommate_data)
    return render(request, 'student/roommate.html', ctx)

@student_required
def application_view(request):
    app_data = cache.get('student_application_data')
    if not app_data:
        student = Student.objects.filter(student_id='STU-204810').first()
        app = Application.objects.filter(student=student).first() if student else None
        preferences = list(app.preferences.all().select_related('hostel')) if app else []
        hostels = list(Hostel.objects.all())
        app_data = {
            'student': student,
            'application': app,
            'preferences': preferences,
            'hostels': hostels,
        }
        cache.set('student_application_data', app_data, 180)

    ctx = get_base_context(request, 'application', is_admin=False)
    ctx.update(app_data)
    return render(request, 'student/application.html', ctx)

@student_required
def status_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()
    
    status_data = cache.get(f"student_status_data_{student.student_id if student else 'none'}")
    if not status_data:
        app = Application.objects.filter(student=student).first() if student else None
        letter = AllocationLetter.objects.filter(student=student).order_by('-generated_at').first() if student else None
        published_run = AllocationRun.objects.filter(status='published').order_by('-created_at').first()
        
        is_allocated = (app and app.status == 'allocated') or (letter is not None) or (published_run is not None)

        if is_allocated and not letter and student:
            letter = AllocationLetter.objects.create(
                letter_id=f"LET-2025-{student.student_id.split('-')[-1]}",
                student=student,
                run=published_run,
                hostel_name="Cedar House",
                room_number="C-214",
                bed_letter="A",
                room_type="Single Ensuite",
                fee_category="Standard Academic",
                move_in_date="20 October 2025"
            )

        status_data = {
            'student': student,
            'application': app,
            'letter': letter,
            'is_allocated': is_allocated,
        }
        cache.set(f"student_status_data_{student.student_id if student else 'none'}", status_data, 180)

    ctx = get_base_context(request, 'status', is_admin=False)
    ctx.update(status_data)
    return render(request, 'student/status.html', ctx)

@student_required
def student_letter_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()
    letter = AllocationLetter.objects.filter(student=student).order_by('-generated_at').first() if student else None
    if not letter and student:
        run = AllocationRun.objects.filter(status='published').order_by('-created_at').first() or AllocationRun.objects.first()
        letter = AllocationLetter.objects.create(
            letter_id=f"LET-2025-{student.student_id.split('-')[-1]}",
            student=student,
            run=run,
            hostel_name="Cedar House",
            room_number="C-214",
            bed_letter="A",
            room_type="Single Ensuite",
            fee_category="Standard Academic",
            move_in_date="20 October 2025"
        )
    return render(request, 'student/allocation_letter.html', {'letter': letter, 'student': student})

@student_required
@require_POST
def submit_room_change_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()
    reason_cat = request.POST.get('reason_category', 'other')
    preferred_hostel = request.POST.get('preferred_hostel', 'Maple Court')
    details = request.POST.get('details', '').strip()

    if student:
        RoomChangeRequest.objects.create(
            student=student,
            current_bed_label="Cedar House · Room C-214A",
            preferred_hostel=preferred_hostel,
            reason_category=reason_cat,
            details=details,
            status='pending'
        )
        actor_name = request.user.get_full_name() or student.name
        AuditLog.objects.create(
            action=f"Room change request submitted by {student.name} ({student.student_id}) for {preferred_hostel} ({reason_cat})",
            actor=actor_name
        )
        invalidate_student_caches()
        messages.success(request, "Your room change request has been submitted for Warden review.")
    return redirect('status')

@student_required
def applications_view(request):
    current_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    from housing.views import get_mock_applications
    apps_list = get_mock_applications(filter_val=current_filter, search_query=search_query)

    profile = getattr(request.user, 'profile', None)
    is_admin = request.user.is_staff or (profile and profile.is_admin())
    ctx = get_base_context(request, 'applications', is_admin=is_admin)
    ctx.update({
        'applications_list': apps_list,
        'current_filter': current_filter,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/applications.html', ctx)

@student_required
def waiting_list_view(request):
    current_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    from housing.views import get_mock_waitlist
    waitlist_items = get_mock_waitlist(filter_val=current_filter, search_query=search_query)

    profile = getattr(request.user, 'profile', None)
    is_admin = request.user.is_staff or (profile and profile.is_admin())
    ctx = get_base_context(request, 'waiting', is_admin=is_admin)
    ctx.update({
        'waitlist_items': waitlist_items,
        'current_filter': current_filter,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/waiting_list.html', ctx)

@student_required
def placeholder_view(request, section):
    if section == 'applications':
        return applications_view(request)
    elif section in ('waiting', 'waitlist'):
        return waiting_list_view(request)
    elif section == 'reports':
        from admin.views import reports_view
        return reports_view(request)
    elif section == 'audit':
        from admin.views import audit_view
        return audit_view(request)

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
                invalidate_student_caches()
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
