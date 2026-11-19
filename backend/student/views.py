import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache

from housing.models import (
    Hostel, Student, Application, ApplicationPreference, AllocationCycle,
    RoommateProfile, RoommateSuggestion, Notification,
    AllocationLetter, RoomChangeRequest, AllocationRun, AuditLog
)
from housing.decorators import student_required
from housing.views import get_base_context, invalidate_student_caches

@student_required
def overview(request):
    ctx = get_base_context(request, 'overview', is_admin=False)
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()

    app = Application.objects.filter(student=student).first() if student else None
    preferences = list(app.preferences.all().select_related('hostel').order_by('rank')) if app else []
    top_pref = preferences[0].hostel.name if preferences else 'Boys Hostel 1'
    top_pref_room = app.room_type_preference if app else 'Single room'
    is_submitted = app and app.status in ('submitted', 'under_review', 'allocated')

    overview_data = {
        'student': student,
        'application': app,
        'is_submitted': is_submitted,
        'hostels': list(Hostel.objects.all()[:2]),
        'preferences': preferences,
        'top_preference': top_pref,
        'top_preference_room': top_pref_room,
        'preferences_count': len(preferences) if preferences else 3,
        'notifications': ctx.get('notifications', [])[:3],
    }

    ctx.update(overview_data)
    return render(request, 'student/overview.html', ctx)

@student_required
def hostels_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()

    # Check if student completed roommate matching quiz
    is_completed = request.session.get('roommate_quiz_completed', False)
    if not is_completed and student:
        is_completed = AuditLog.objects.filter(
            actor=student.name, action__icontains="Roommate matching quiz completed"
        ).exists()
        if is_completed:
            request.session['roommate_quiz_completed'] = True

    proceed_override = request.GET.get('proceed') == '1' or request.session.get('roommate_prompt_dismissed', False)
    needs_roommate_quiz = (not is_completed) and (not proceed_override)

    query = request.GET.get('q', '').strip()
    all_hostels = cache.get('all_hostels_list')
    if not all_hostels:
        all_hostels = list(Hostel.objects.all())
        cache.set('all_hostels_list', all_hostels, 1800)

    if query:
        hostels_qs = [h for h in all_hostels if query.lower() in h.name.lower()]
    else:
        hostels_qs = all_hostels

    ctx = get_base_context(request, 'hostels', is_admin=False)
    ctx.update({
        'hostels': hostels_qs,
        'search_query': query,
        'total_available': sum(h.beds_available for h in hostels_qs),
        'needs_roommate_quiz': needs_roommate_quiz,
        'is_roommate_completed': is_completed,
    })
    return render(request, 'student/hostels.html', ctx)

@student_required
@require_POST
def api_dismiss_roommate_prompt(request):
    request.session['roommate_prompt_dismissed'] = True
    return JsonResponse({'status': 'ok'})

@student_required
def roommate_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()

    is_completed = request.session.get('roommate_quiz_completed', False)
    if not is_completed and student:
        is_completed = AuditLog.objects.filter(
            actor=student.name, action__icontains="Roommate matching quiz completed"
        ).exists()
        if is_completed:
            request.session['roommate_quiz_completed'] = True

    cache_key = f"student_roommate_data_{student.student_id if student else 'default'}"
    roommate_data = cache.get(cache_key)
    if not roommate_data:
        matches = list(RoommateSuggestion.objects.filter(target_student=student).select_related('suggested_student', 'target_student')) if student else []
        roommate_data = {
            'matches': matches,
            'student': student,
        }
        cache.set(cache_key, roommate_data, 1800)

    ctx = get_base_context(request, 'roommate', is_admin=False)
    ctx.update(roommate_data)
    ctx.update({
        'is_completed': is_completed,
        'auto_start': request.GET.get('start') == '1' or request.GET.get('prompt') == '1',
        'next_url': request.GET.get('next', reverse('hostels')),
    })
    return render(request, 'student/roommate.html', ctx)

@student_required
@require_POST
def submit_roommate_quiz_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()

    sleep_schedule = request.POST.get('sleep_schedule', '10 PM – 12 AM').strip()
    cleanliness = request.POST.get('cleanliness', 'Generally tidy').strip()
    noise_level = request.POST.get('noise_level', 'Low background noise').strip()
    interests = request.POST.get('interests', 'Computer Science · Web Design · Reading').strip()

    if student:
        rp, created = RoommateProfile.objects.get_or_create(
            student=student,
            defaults={
                'sleep_schedule': sleep_schedule,
                'cleanliness': cleanliness,
                'noise_level': noise_level,
                'interests': interests,
                'is_active': True
            }
        )
        if not created:
            rp.sleep_schedule = sleep_schedule
            rp.cleanliness = cleanliness
            rp.noise_level = noise_level
            rp.is_active = True
            rp.save()

        actor_name = request.user.get_full_name() or student.name
        AuditLog.objects.create(
            action=f"Roommate matching quiz completed by {student.name} ({student.student_id})",
            actor=actor_name
        )

    request.session['roommate_quiz_completed'] = True
    invalidate_student_caches()

    return JsonResponse({
        'status': 'success',
        'message': 'Roommate matching questionnaire completed successfully.',
        'redirect_url': reverse('hostels')
    })

@student_required
def application_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else None
    cache_key = f"student_application_data_{student.student_id if student else 'default'}"
    app_data = cache.get(cache_key)
    if not app_data:
        if not student:
            student = Student.objects.filter(student_id='STU-204810').first()
        app = Application.objects.filter(student=student).first() if student else None
        preferences = list(app.preferences.all().select_related('hostel').order_by('rank')) if app else []
        hostels = list(Hostel.objects.all().order_by('name'))
        
        name_parts = (student.name or '').split() if student else []
        first_name = name_parts[0] if name_parts else 'Amara'
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Mensah'
        is_submitted = app is not None and app.status in ('submitted', 'under_review', 'allocated')

        app_data = {
            'student': student,
            'first_name': first_name,
            'last_name': last_name,
            'application': app,
            'is_submitted': is_submitted,
            'preferences': preferences,
            'hostels': hostels,
        }
        cache.set(cache_key, app_data, 1800)

    ctx = get_base_context(request, 'application', is_admin=False)
    ctx.update(app_data)
    return render(request, 'student/application.html', ctx)

@student_required
@require_POST
def submit_application_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else None
    if not student:
        student = Student.objects.filter(student_id='STU-204810').first()

    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    programme = request.POST.get('programme', '').strip()
    study_mode = request.POST.get('study_mode', 'Full-time student').strip()
    special_reqs = request.POST.get('special_requirements', '').strip()
    additional_info = request.POST.get('additional_info', '').strip()
    room_pref = request.POST.get('room_pref', 'Single room').strip()
    bathroom_pref = request.POST.get('bathroom_pref', 'Private Ensuite').strip()
    floor_pref = request.POST.get('preferred_floor', 'No preference').strip()
    accessibility_reqs = request.POST.get('accessibility_reqs', '').strip()

    raw_prefs = request.POST.get('hostel_preferences', '')
    ranked_hostel_names = []
    if raw_prefs:
        try:
            parsed = json.loads(raw_prefs)
            if isinstance(parsed, list):
                ranked_hostel_names = parsed
        except Exception:
            ranked_hostel_names = [p.strip() for p in raw_prefs.split(',') if p.strip()]

    if not ranked_hostel_names:
        ranked_hostel_names = request.POST.getlist('preferences[]') or request.POST.getlist('preferences')

    if not ranked_hostel_names:
        ranked_hostel_names = ['Boys Hostel 1', 'Boys Hostel 2', 'Boys Hostel 3']

    if student:
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            student.name = full_name
            parts = full_name.split()
            student.avatar_initials = ''.join(p[0].upper() for p in parts[:2])
            if request.user:
                request.user.first_name = first_name
                request.user.last_name = last_name
                try:
                    request.user.save(update_fields=['first_name', 'last_name'])
                except Exception:
                    pass
        if programme:
            student.programme = programme
        student.save()

    cycle = AllocationCycle.objects.filter(is_active=True).first()

    notes_parts = []
    if additional_info:
        notes_parts.append(f"Notes: {additional_info}")
    if special_reqs:
        notes_parts.append(f"Special: {special_reqs}")
    if accessibility_reqs:
        notes_parts.append(f"Access: {accessibility_reqs}")
    if bathroom_pref:
        notes_parts.append(f"Bath: {bathroom_pref}")
    if floor_pref and floor_pref != 'No preference':
        notes_parts.append(f"Floor: {floor_pref}")
    notes_combined = " · ".join(notes_parts)

    app, created = Application.objects.get_or_create(
        student=student,
        defaults={
            'application_id': f"NST-25-{random.randint(10000, 99999)}",
            'cycle': cycle,
            'academic_year': '2025/26',
            'quota': 'Continuing Students',
            'status': 'submitted',
            'progress_percentage': 100,
            'current_step': 5,
            'room_type_preference': room_pref,
            'additional_notes': notes_combined,
            'submitted_at': timezone.now()
        }
    )

    if not created:
        app.status = 'submitted'
        app.progress_percentage = 100
        app.current_step = 5
        app.room_type_preference = room_pref
        app.additional_notes = notes_combined
        app.submitted_at = timezone.now()
        if cycle and not app.cycle:
            app.cycle = cycle
        app.save()

    ApplicationPreference.objects.filter(application=app).delete()

    saved_prefs = []
    for rank_idx, h_name in enumerate(ranked_hostel_names, start=1):
        clean_name = str(h_name).strip()
        hostel = Hostel.objects.filter(name__iexact=clean_name).first()
        if not hostel:
            hostel = Hostel.objects.filter(name__icontains=clean_name).first()
        if hostel:
            ApplicationPreference.objects.create(
                application=app,
                hostel=hostel,
                rank=rank_idx
            )
            saved_prefs.append({
                'rank': rank_idx,
                'hostel': hostel.name
            })

    actor_name = request.user.get_full_name() or (student.name if student else 'Student')
    AuditLog.objects.create(
        action=f"Application {app.application_id} submitted by {student.name} ({student.student_id}) with {len(saved_prefs)} ranked preferences ({room_pref})",
        actor=actor_name
    )

    invalidate_student_caches()

    try:
        from housing.sockets import sio
        sio.emit('new_activity', {
            'action': f"New Application {app.application_id} submitted",
            'actor': student.name if student else 'Student',
            'time': 'Just now'
        })
    except Exception:
        pass

    return JsonResponse({
        'status': 'success',
        'application_id': app.application_id,
        'student_name': student.name if student else 'Student',
        'top_preference': saved_prefs[0]['hostel'] if saved_prefs else 'Boys Hostel 1',
        'room_preference': room_pref,
        'preferences': saved_prefs,
        'message': 'Your application has been successfully saved to the database.'
    })

@student_required
def status_view(request):
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()
    
    cache_key = f"student_status_data_{student.student_id if student else 'none'}"
    status_data = cache.get(cache_key)
    if not status_data:
        app = Application.objects.filter(student=student).first() if student else None
        preferences = list(app.preferences.all().select_related('hostel').order_by('rank')) if app else []
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
            'preferences': preferences,
            'letter': letter,
            'is_allocated': is_allocated,
        }
        cache.set(cache_key, status_data, 1800)

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

@student_required
def hostel_change_view(request):
    """
    Hostel Change Request & Residential Booking Change Workflow (Session 2026-2027)
    Allows allocated students to select Room Types, Seater Categories, and Hostels
    with live difference pricing, contact verification, and direct undertaking settlement.
    """
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else None
    if not student:
        student = Student.objects.filter(student_id='STU-204810').first()

    letter = AllocationLetter.objects.filter(student=student).order_by('-generated_at').first() if student else None

    current_allocation = {
        'hostel': 'Boys Hostel-01',
        'seater': 'Standard Air Conditioned 4 Seater',
        'room_no': f"{letter.room_number if letter else 'A914'}-Bed {letter.bed_letter if letter else 'D'}",
        'availing_food': 'Yes',
        'meal_type': 'Standard Mess Two Meals',
        'food_type': 'Combo North-South',
        'mess_name': 'Same Hostel Mess 1(BH-01)',
        'availing_laundry': 'No',
        'availing_gym': 'No',
        'current_credit': 119450,  # Fee baseline for difference calculation
    }

    room_types = [
        {
            'id': 'studio_ac',
            'name': 'Studio Apartment Air Conditioned',
            'washroom': 'Attached Washroom',
            'is_default': True,
        },
        {
            'id': 'standard_ac',
            'name': 'Standard Air Conditioned',
            'washroom': 'Attached Washroom',
            'is_default': False,
        },
        {
            'id': 'standard_cooler',
            'name': 'Standard Air Cooled',
            'washroom': 'Attached Washroom',
            'is_default': False,
        },
    ]

    seater_packages = {
        'studio_ac': [
            {
                'id': 'studio_2_pantry',
                'name': 'Studio Apartment Air Conditioned 2 Seater (With Pantry)',
                'badge': 'Limited Seats Left',
                'price': 150000,
                'is_default': True,
                'available_seats': 4,
            },
            {
                'id': 'studio_3_pantry',
                'name': 'Studio Apartment Air Conditioned 3 Seater (With Pantry)',
                'badge': 'Limited Seats Left',
                'price': 130000,
                'is_default': False,
                'available_seats': 7,
            },
            {
                'id': 'studio_4_seater',
                'name': 'Studio Apartment Air Conditioned 4 Seater',
                'badge': 'Available',
                'price': 105000,
                'is_default': False,
                'available_seats': 12,
            },
            {
                'id': 'studio_3_seater',
                'name': 'Studio Apartment Air Conditioned 3 Seater',
                'badge': 'Available',
                'price': 120000,
                'is_default': False,
                'available_seats': 9,
            },
        ],
        'standard_ac': [
            {
                'id': 'std_ac_1',
                'name': 'Standard Air Conditioned 1 Seater (Attached Washroom)',
                'badge': 'Few Remaining',
                'price': 160000,
                'is_default': False,
                'available_seats': 2,
            },
            {
                'id': 'std_ac_2',
                'name': 'Standard Air Conditioned 2 Seater (Attached Washroom)',
                'badge': 'Available',
                'price': 125000,
                'is_default': False,
                'available_seats': 15,
            },
            {
                'id': 'std_ac_3',
                'name': 'Standard Air Conditioned 3 Seater (Attached Washroom)',
                'badge': 'Available',
                'price': 105000,
                'is_default': False,
                'available_seats': 21,
            },
            {
                'id': 'std_ac_4',
                'name': 'Standard Air Conditioned 4 Seater (Attached Washroom)',
                'badge': 'High Availability',
                'price': 90000,
                'is_default': False,
                'available_seats': 34,
            },
        ],
        'standard_cooler': [
            {
                'id': 'std_cooler_2',
                'name': 'Standard Air Cooled 2 Seater (Attached Washroom)',
                'badge': 'Available',
                'price': 95000,
                'is_default': False,
                'available_seats': 8,
            },
            {
                'id': 'std_cooler_3',
                'name': 'Standard Air Cooled 3 Seater (Attached Washroom)',
                'badge': 'Available',
                'price': 82000,
                'is_default': False,
                'available_seats': 18,
            },
            {
                'id': 'std_cooler_4',
                'name': 'Standard Air Cooled 4 Seater (Attached Washroom)',
                'badge': 'High Availability',
                'price': 72000,
                'is_default': False,
                'available_seats': 45,
            },
        ]
    }

    hostel_options = [
        {'id': 'bs11', 'name': 'Boys Studios 11', 'is_default': True, 'type': 'Studio Apartment'},
        {'id': 'bh1', 'name': 'Boys Hostel 1 - Wing B', 'is_default': False, 'type': 'Standard AC'},
        {'id': 'bh2', 'name': 'Boys Hostel 2 (BH-02)', 'is_default': False, 'type': 'Studio Apartment'},
        {'id': 'bh3', 'name': 'Boys Hostel 3 (BH-03)', 'is_default': False, 'type': 'Ensuite AC'},
        {'id': 'bh4', 'name': 'Boys Hostel 4 (BH-04)', 'is_default': False, 'type': 'Standard Air Cooled'},
    ]

    # Pre-filled contact info
    student_phone = student.phone if (student and student.phone) else '9141773450'
    student_email = student.email if (student and student.email) else (request.user.email or 'harsha.bk23@lpu.in')

    ctx = get_base_context(request, 'hostel-change', is_admin=False)
    ctx.update({
        'student': student,
        'current_allocation': current_allocation,
        'room_types': room_types,
        'seater_packages': seater_packages,
        'seater_packages_json': json.dumps(seater_packages),
        'hostel_options': hostel_options,
        'student_mobile': student_phone,
        'student_email': student_email,
        'initial_net_payable': 30550,
    })
    return render(request, 'student/hostel_change.html', ctx)

@student_required
@require_POST
def submit_hostel_change_request(request):
    """
    Handles payment undertaking & booking change submission.
    Creates RoomChangeRequest, immutable AuditLog, and triggers real-time notice.
    """
    profile = getattr(request.user, 'profile', None)
    student = profile.student_profile if (profile and profile.student_profile) else Student.objects.filter(student_id='STU-204810').first()

    room_type = request.POST.get('room_type', 'Studio Apartment Air Conditioned')
    seater_name = request.POST.get('seater_name', 'Studio Apartment Air Conditioned 2 Seater (With Pantry)')
    seater_price = request.POST.get('seater_price', '150000.00')
    hostel_name = request.POST.get('hostel_name', 'Boys Studios 11')
    net_payable = request.POST.get('net_payable', '30550')
    mobile = request.POST.get('mobile', student.phone if student else '9141773450')
    email = request.POST.get('email', student.email if student else 'harsha.bk23@lpu.in')
    current_bed = request.POST.get('current_bed', 'Boys Hostel-01 · A914-Bed D')

    ref_code = f"HCR-2026-{random.randint(1000, 9999)}"

    details_payload = json.dumps({
        'reference_code': ref_code,
        'session': '2026-2027',
        'room_type': room_type,
        'seater_category': seater_name,
        'package_price': seater_price,
        'net_payable_amount': net_payable,
        'student_mobile': mobile,
        'student_email': email,
        'undertaking_confirmed': True,
        'submitted_at': timezone.now().strftime('%d %b %Y, %H:%M:%S UTC'),
    })

    if student:
        req_obj = RoomChangeRequest.objects.create(
            student=student,
            current_bed_label=current_bed,
            preferred_hostel=hostel_name,
            reason_category='financial',
            details=details_payload,
            status='pending'
        )

        AuditLog.objects.create(
            action=f"Hostel Change Request {ref_code} confirmed by {student.name} ({student.student_id}) for {hostel_name} · {seater_name} (Net Payable: ₹{net_payable})",
            actor=student.name,
        )

        try:
            from housing.sockets import sio
            sio.emit('new_activity', {
                'action': f"New Hostel Change Request {ref_code}",
                'actor': student.name,
                'time': 'Just now'
            })
        except Exception:
            pass

    return JsonResponse({
        'status': 'success',
        'message': 'Hostel Change Request & Residential Booking submitted successfully.',
        'reference_code': ref_code,
        'net_payable': net_payable,
        'seater_name': seater_name,
        'hostel_name': hostel_name,
        'redirect_url': reverse('status'),
    })

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
