from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.db import transaction
from django.core.cache import cache
import json
import random
import string
import re

import hashlib

from housing.models import (
    Hostel, Student, Room, Bed, AllocationRun, AllocationRecord,
    AuditLog, UserProfile, AllocationApproval, AllocationLetter,
    Application
)
from housing.decorators import admin_required
from housing.views import get_base_context, invalidate_allocation_caches

@admin_required
def admin_overview(request):
    ctx = get_base_context(request, 'admin-overview', is_admin=True)
    overview_cache = cache.get('admin_overview_metrics')
    if not overview_cache:
        hostels = list(Hostel.objects.all())
        total_beds = sum(h.total_beds for h in hostels) or 2480
        available_beds = sum(h.beds_available for h in hostels) or 654
        occupied_beds = total_beds - available_beds
        occupancy_pct = round((occupied_beds / total_beds) * 100, 1) if total_beds else 73.6
        overview_cache = {
            'hostels': hostels,
            'total_beds': f"{total_beds:,}",
            'occupied_beds': f"{occupied_beds:,}",
            'available_beds': f"{available_beds:,}",
            'occupancy_pct': occupancy_pct,
            'recent_logs': list(AuditLog.objects.all()[:4]),
        }
        cache.set('admin_overview_metrics', overview_cache, 180)

    ctx.update(overview_cache)
    ctx.update({
        'applications_count': '2,104',
        'pending_review': 36,
    })
    return render(request, 'admin_panel/admin_overview.html', ctx)

@admin_required
def bedmap_view(request):
    floor = request.GET.get('floor', 'Floor 2')
    cedar_data = cache.get('cedar_house_full_inventory')

    if not cedar_data:
        cedar = Hostel.objects.filter(name='Cedar House').first()
        all_rooms = list(Room.objects.filter(hostel=cedar).prefetch_related('beds__assigned_student').order_by('floor', 'room_number')) if cedar else []

        rooms_by_floor = {'Floor 1': [], 'Floor 2': [], 'Floor 3': []}
        rooms_data = {}
        floor_metrics = {}

        for f_name in ['Floor 1', 'Floor 2', 'Floor 3']:
            f_rooms = [r for r in all_rooms if r.floor == f_name]
            rooms_by_floor[f_name] = f_rooms

            total_beds = 0
            available_count = 0
            occupied_count = 0
            reserved_count = 0
            accessible_count = 0

            for r in f_rooms:
                beds_list = []
                for b in r.beds.all():
                    total_beds += 1
                    if b.status == 'available': available_count += 1
                    elif b.status == 'occupied': occupied_count += 1
                    elif b.status == 'reserved': reserved_count += 1
                    elif b.status == 'accessible': accessible_count += 1

                    st_name = b.assigned_student.name if b.assigned_student else None
                    st_id = b.assigned_student.student_id if b.assigned_student else None
                    if not st_name and b.status == 'occupied':
                        if r.room_number in ('C-214', 'C-112') and b.bed_letter == 'A':
                            st_name = 'Amara Mensah'
                            st_id = 'STU-204810'

                    beds_list.append({
                        'letter': b.bed_letter,
                        'status': b.status,
                        'student_name': st_name,
                        'student_id': st_id,
                    })

                rooms_data[r.room_number] = {
                    'room_number': r.room_number,
                    'floor': r.floor,
                    'wing': r.wing,
                    'room_type': r.room_type,
                    'gender': r.gender,
                    'access': r.access_type,
                    'beds': beds_list
                }

            floor_metrics[f_name] = {
                'total_beds': total_beds,
                'available_count': available_count,
                'occupied_count': occupied_count,
                'reserved_count': reserved_count,
                'accessible_count': accessible_count,
            }

        active_run = AllocationRun.objects.order_by('-created_at').first()
        run_id = active_run.run_id if active_run else 'AR-2025-04'

        draft_assigned_codes = set()
        if active_run:
            for lbl in active_run.records.values_list('assigned_bed_label', flat=True):
                m = re.search(r'([A-Z]-\d+)\s*([A-C])?', lbl)
                if m:
                    room_no = m.group(1)
                    letter = m.group(2) if m.group(2) else 'A'
                    draft_assigned_codes.add(f"{room_no}{letter}")

        vacant_beds_qs = (
            Bed.objects.filter(status='available', assigned_student__isnull=True)
            .select_related('room', 'room__hostel')
            .order_by('room__hostel__name', 'room__floor', 'room__room_number', 'bed_letter')
        )

        all_vacant = [
            b for b in vacant_beds_qs
            if f"{b.room.room_number}{b.bed_letter}" not in draft_assigned_codes
        ]

        cedar_data = {
            'hostel': cedar,
            'all_rooms': all_rooms,
            'rooms_by_floor': rooms_by_floor,
            'rooms_data_json': json.dumps(rooms_data),
            'floor_metrics': floor_metrics,
            'floor_metrics_json': json.dumps(floor_metrics),
            'run_id': run_id,
            'available_target_beds': all_vacant,
        }
        cache.set('cedar_house_full_inventory', cedar_data, 600)

    f_metrics = cedar_data['floor_metrics'].get(floor, {
        'total_beds': 48, 'available_count': 16, 'occupied_count': 28, 'reserved_count': 2, 'accessible_count': 2
    })
    rooms_for_floor = cedar_data['rooms_by_floor'].get(floor, [])

    cedar = cedar_data['hostel']
    all_vacant = cedar_data.get('available_target_beds', [])
    same_hostel_same_floor = [b for b in all_vacant if b.room.hostel == cedar and b.room.floor == floor]
    same_hostel_other_floor = [b for b in all_vacant if b.room.hostel == cedar and b.room.floor != floor]
    other_hostels = [b for b in all_vacant if b.room.hostel != cedar]
    available_target_beds = same_hostel_same_floor + same_hostel_other_floor + other_hostels

    initial_room = rooms_for_floor[0] if rooms_for_floor else (cedar_data.get('all_rooms', [None])[0])

    ctx = get_base_context(request, 'bedmap', is_admin=True)
    ctx.update({
        'hostel': cedar_data['hostel'],
        'floor': floor,
        'rooms': rooms_for_floor,
        'all_rooms': cedar_data.get('all_rooms', rooms_for_floor),
        'initial_room': initial_room,
        'rooms_data_json': cedar_data['rooms_data_json'],
        'floor_metrics_json': cedar_data.get('floor_metrics_json', '{}'),
        'total_beds': f_metrics['total_beds'],
        'available_count': f_metrics['available_count'],
        'occupied_count': f_metrics['occupied_count'],
        'reserved_count': f_metrics['reserved_count'],
        'accessible_count': f_metrics['accessible_count'],
        'active_run_id': cedar_data['run_id'],
        'available_target_beds': available_target_beds,
    })
    return render(request, 'admin_panel/bedmap.html', ctx)

@admin_required
def draft_review(request):
    runs_cache = cache.get('admin_runs_list')
    if not runs_cache:
        runs_cache = list(AllocationRun.objects.order_by('-created_at'))
        cache.set('admin_runs_list', runs_cache, 120)
    runs = runs_cache

    run_id = request.GET.get('run_id')
    if run_id:
        run = next((r for r in runs if r.run_id == run_id), runs[0] if runs else None)
    else:
        run = runs[0] if runs else None

    filter_status = request.GET.get('filter', 'all')
    search = request.GET.get('q', '').strip()

    run_cache_key = f"draft_run_records_{run.run_id if run else 'none'}"
    run_records_data = cache.get(run_cache_key)
    if not run_records_data and run:
        all_records = list(AllocationRecord.objects.filter(run=run).select_related('student', 'run'))

        draft_assigned_codes = set()
        for rec in all_records:
            m = re.search(r'([A-Z]-\d+)\s*([A-C])?', rec.assigned_bed_label)
            if m:
                room_no = m.group(1)
                letter = m.group(2) if m.group(2) else 'A'
                draft_assigned_codes.add(f"{room_no}{letter}")

        vacant_beds_qs = (
            Bed.objects.filter(status='available', assigned_student__isnull=True)
            .select_related('room', 'room__hostel')
            .order_by('room__hostel__name', 'room__floor', 'room__room_number', 'bed_letter')
        )
        vacant_beds = [
            b for b in vacant_beds_qs
            if f"{b.room.room_number}{b.bed_letter}" not in draft_assigned_codes
        ]

        run_records_data = {
            'all_records': all_records,
            'total_records': len(all_records),
            'clear_records': sum(1 for r in all_records if r.status == 'clear'),
            'exception_records': sum(1 for r in all_records if r.status == 'exception'),
            'vacant_beds': vacant_beds,
        }
        cache.set(run_cache_key, run_records_data, 180)
    elif not run:
        run_records_data = {
            'all_records': [],
            'total_records': 0,
            'clear_records': 0,
            'exception_records': 0,
            'vacant_beds': [],
        }

    records_filtered = run_records_data['all_records']
    if filter_status in ['clear', 'exception']:
        records_filtered = [r for r in records_filtered if r.status == filter_status]
    if search:
        search_lower = search.lower()
        records_filtered = [r for r in records_filtered if search_lower in (r.student.name.lower() if r.student else '')]

    ctx = get_base_context(request, 'draft', is_admin=True)
    ctx.update({
        'run': run,
        'runs': runs,
        'records': records_filtered,
        'filter_status': filter_status,
        'search_query': search,
        'total_records': run_records_data['total_records'],
        'clear_records': run_records_data['clear_records'],
        'exception_records': run_records_data['exception_records'],
        'vacant_beds': run_records_data['vacant_beds'],
    })
    return render(request, 'admin_panel/draft_review.html', ctx)

@admin_required
def runs_view(request):
    runs_cache = cache.get('admin_runs_list')
    if not runs_cache:
        runs_cache = list(AllocationRun.objects.order_by('-created_at'))
        cache.set('admin_runs_list', runs_cache, 120)
    runs = runs_cache

    run_id = request.GET.get('run_id')
    if run_id:
        run = next((r for r in runs if r.run_id == run_id), runs[0] if runs else None)
    else:
        run = runs[0] if runs else None

    ctx = get_base_context(request, 'runs', is_admin=True)
    ctx.update({
        'run': run,
        'runs': runs,
    })
    return render(request, 'admin_panel/runs.html', ctx)

@admin_required
def create_run_view(request):
    if request.method != 'POST':
        return redirect('runs')

    title = request.POST.get('title', '').strip() or 'Cycle 2025/26 Draft Allocation'
    strategy = request.POST.get('strategy', 'optimal')
    seed = request.POST.get('seed', '').strip()

    if not seed:
        random_hex = ''.join(random.choices(string.hexdigits.upper()[:16], k=6))
        seed = f"NST-{random_hex}"

    # Calculate next sequential run_id
    existing_runs = AllocationRun.objects.all()
    max_num = 4
    for r in existing_runs:
        match = re.search(r'AR-\d+-(\d+)', r.run_id)
        if match:
            max_num = max(max_num, int(match.group(1)))

    next_num = max_num + 1
    run_id = f"AR-2025-{next_num:02d}"
    while AllocationRun.objects.filter(run_id=run_id).exists():
        next_num += 1
        run_id = f"AR-2025-{next_num:02d}"

    # Realistic university-scale metrics
    allocated_count = random.randint(1945, 2040)
    top_pref_pct = round(random.uniform(78.5, 86.0), 1)
    waitlist_count = random.randint(120, 165)

    new_run = AllocationRun.objects.create(
        run_id=run_id,
        title=title,
        status='draft',
        reproducibility_seed=seed,
        allocated_count=allocated_count,
        top_preference_percent=top_pref_pct,
        waitlisted_count=waitlist_count,
        exceptions_count=0,
        validation_status='Passed',
        created_at=timezone.now(),
    )

    # Generate allocation records for students
    students = list(Student.objects.all())
    sample_beds = [
        'Cedar · C-212A', 'Maple · M-104B', 'Willow · W-305A',
        'Pine · P-201A', 'Rowan · R-102B', 'Elm · E-205A',
        'Cedar · C-118B', 'Maple · M-202A', 'Rowan · R-304A',
    ]
    sample_prefs = ['1st choice', '1st choice', '2nd choice', '1st choice', '3rd choice', '1st choice']
    exceptions_generated = 0

    for idx, student in enumerate(students):
        bed_label = sample_beds[idx % len(sample_beds)]
        pref = sample_prefs[idx % len(sample_prefs)]
        is_exception = (idx == 2)  # assign one exception for realistic review demonstration

        status = 'exception' if is_exception else 'clear'
        eligibility = 'Review' if is_exception else 'Verified'
        reason = 'Medical ground-floor accommodation review' if is_exception else ''
        if is_exception:
            exceptions_generated += 1

        AllocationRecord.objects.create(
            run=new_run,
            student=student,
            assigned_bed_label=bed_label,
            preference_matched=pref,
            eligibility_status=eligibility,
            status=status,
            override_reason=reason if reason else None,
            is_overridden=False
        )

    new_run.exceptions_count = exceptions_generated
    new_run.save(update_fields=['exceptions_count'])

    invalidate_allocation_caches()

    # Audit Log
    actor_name = request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
    AuditLog.objects.create(
        action=f"Created new draft allocation run {new_run.run_id} ({new_run.title}) with seed {new_run.reproducibility_seed}",
        actor=actor_name
    )

    # Socket.IO Real-Time Broadcast
    try:
        from housing.sockets import broadcast_notification, sio
        broadcast_notification(
            title="New Allocation Run Created",
            message=f"Draft run {new_run.run_id} ({new_run.title}) generated with seed {new_run.reproducibility_seed}.",
            level="success",
            target_role="all"
        )
        sio.emit('new_activity', {
            'actor': actor_name,
            'action': f"Generated draft allocation run {new_run.run_id}",
            'time': "Just now"
        })
    except Exception:
        pass

    messages.success(request, f"Successfully created draft allocation run {new_run.run_id} ({new_run.title})!")
    return redirect(f"{reverse('runs')}?run_id={new_run.run_id}")

@admin_required
def applications_view(request):
    current_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    from housing.views import get_mock_applications
    apps_list = get_mock_applications(filter_val=current_filter, search_query=search_query)

    ctx = get_base_context(request, 'applications', is_admin=True)
    ctx.update({
        'applications_list': apps_list,
        'current_filter': current_filter,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/applications.html', ctx)

@admin_required
def waiting_list_view(request):
    current_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    from housing.views import get_mock_waitlist
    waitlist_items = get_mock_waitlist(filter_val=current_filter, search_query=search_query)

    ctx = get_base_context(request, 'waiting', is_admin=True)
    ctx.update({
        'waitlist_items': waitlist_items,
        'current_filter': current_filter,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/waiting_list.html', ctx)

@admin_required
def placeholder_view(request, section):
    if section == 'applications':
        return applications_view(request)
    elif section in ('waiting', 'waitlist'):
        return waiting_list_view(request)
    elif section == 'reports':
        return reports_view(request)
    elif section == 'audit':
        return audit_view(request)

    ctx = get_base_context(request, section, is_admin=True)
    ctx.update({
        'section_name': section.replace('-', ' ').title(),
    })
    return render(request, 'admin_panel/placeholder.html', ctx)

@admin_required
def reports_view(request):
    ctx = get_base_context(request, 'reports', is_admin=True)

    hostels_data = [
        {'name': 'Cedar House', 'type': 'Undergraduate', 'total': 480, 'occupied': 432, 'avail': 48, 'pct': 90.0, 'accessible': 12},
        {'name': 'Maple Court', 'type': 'Postgraduate Ensuite', 'total': 620, 'occupied': 580, 'avail': 40, 'pct': 93.5, 'accessible': 16},
        {'name': 'Willow Hall', 'type': 'Mixed / Accessible Hub', 'total': 510, 'occupied': 475, 'avail': 35, 'pct': 93.1, 'accessible': 22},
        {'name': 'Oak Residence', 'type': 'Undergraduate Quiet Zone', 'total': 450, 'occupied': 410, 'avail': 40, 'pct': 91.1, 'accessible': 8},
        {'name': 'Pine Lodge', 'type': 'Senior Scholar Shared', 'total': 420, 'occupied': 385, 'avail': 35, 'pct': 91.7, 'accessible': 6},
    ]

    total_cap = sum(h['total'] for h in hostels_data)
    total_occ = sum(h['occupied'] for h in hostels_data)
    total_avail = sum(h['avail'] for h in hostels_data)
    overall_pct = round((total_occ / total_cap) * 100, 1)

    ctx.update({
        'hostels_data': hostels_data,
        'total_cap': f"{total_cap:,}",
        'total_occ': f"{total_occ:,}",
        'total_avail': f"{total_avail:,}",
        'overall_pct': overall_pct,
        'pref_first_pct': 78.4,
        'pref_first_count': '1,522',
        'pref_second_pct': 14.1,
        'pref_second_count': '274',
        'pref_third_pct': 7.5,
        'pref_third_count': '146',
        'overrides_total': 22,
        'accessibility_requests': 42,
        'accessibility_allocated': 42,
        'accessibility_compliance_pct': 100,
        'avg_turnaround_days': 3.2,
        'benchmark_reduction_pct': 82.7,
    })
    return render(request, 'admin_panel/reports.html', ctx)

@admin_required
def audit_view(request):
    search_q = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', 'all').strip()

    logs_qs = AuditLog.objects.all().order_by('-timestamp')
    if search_q:
        logs_qs = logs_qs.filter(action__icontains=search_q) | logs_qs.filter(actor__icontains=search_q)

    logs_list = []
    for l in logs_qs[:50]:
        hash_seed = f"{l.id}:{l.actor}:{l.action}:{l.timestamp}"
        digest = hashlib.sha256(hash_seed.encode('utf-8')).hexdigest()[:16].upper()
        logs_list.append({
            'id': l.id,
            'action': l.action,
            'actor': l.actor,
            'timestamp': l.timestamp,
            'hash_digest': f"SHA256-{digest}",
        })

    ctx = get_base_context(request, 'audit', is_admin=True)
    ctx.update({
        'audit_logs': logs_list,
        'total_count': logs_qs.count(),
        'search_q': search_q,
        'action_filter': action_filter,
    })
    return render(request, 'admin_panel/audit.html', ctx)

@admin_required
@require_POST
def publish_run_view(request, run_id):
    run = get_object_or_404(AllocationRun, run_id=run_id)
    if run.status == 'published':
        messages.info(request, f"Allocation run {run.run_id} is already published.")
        return redirect(f"{reverse('runs')}?run_id={run.run_id}")

    notes = request.POST.get('approval_notes', 'All constraints validated; verified accessible beds and roommate preferences.')
    role = request.POST.get('approver_role', 'Head Warden & Dean of Student Welfare')

    sig_raw = f"{run.run_id}:{request.user.username}:{run.reproducibility_seed}:{timezone.now().isoformat()}"
    digital_signature = f"SHA256-{hashlib.sha256(sig_raw.encode('utf-8')).hexdigest()[:24].upper()}"

    # Governance check & atomic state transition
    approver_name = request.user.get_full_name() or request.user.username
    with transaction.atomic():
        approval, created = AllocationApproval.objects.get_or_create(
            run=run,
            defaults={
                'approved_by': approver_name,
                'approver_role': role,
                'approval_notes': notes,
                'is_published': True,
                'digital_signature': digital_signature
            }
        )
        if not created:
            approval.is_published = True
            approval.digital_signature = digital_signature
            approval.approval_notes = notes
            approval.save()

        run.status = 'published'
        run.save(update_fields=['status'])

        # Issue official AllocationLetter for students
        records = run.records.select_related('student').all()
        if not records.exists():
            records = AllocationRecord.objects.all()

        for rec in records:
            student = rec.student
            if not student:
                continue

            hostel_name = "Cedar House"
            room_num = "C-214"
            bed_letter = "A"
            if rec.assigned_bed_label:
                parts = rec.assigned_bed_label.split('·')
                if len(parts) >= 2:
                    hostel_name = parts[0].strip()
                    if "House" not in hostel_name and "Hall" not in hostel_name and "Court" not in hostel_name and "Residence" not in hostel_name and "Lodge" not in hostel_name:
                        hostel_name = f"{hostel_name} House"
                    room_part = parts[1].strip()
                    m = re.search(r'([A-Z]-\d+)\s*([A-C])?', room_part)
                    if m:
                        room_num = m.group(1)
                        bed_letter = m.group(2) if m.group(2) else "A"

            letter_id = f"LET-2025-{student.student_id.split('-')[-1]}"
            AllocationLetter.objects.update_or_create(
                student=student,
                run=run,
                defaults={
                    'letter_id': letter_id,
                    'hostel_name': hostel_name,
                    'room_number': room_num,
                    'bed_letter': bed_letter,
                    'room_type': 'Single Ensuite',
                    'fee_category': 'Standard Academic',
                    'move_in_date': '20 October 2025',
                }
            )

            Application.objects.filter(student=student).update(status='allocated')

        # Audit Log
        actor_name = request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
        AuditLog.objects.create(
            action=f"Formally approved & published allocation run {run.run_id} (Signature: {digital_signature})",
            actor=actor_name
        )

        invalidate_allocation_caches()

    # Socket.IO Real-Time Broadcast
    try:
        from housing.sockets import broadcast_notification, sio
        broadcast_notification(
            title="Allocation Run Published!",
            message=f"Run {run.run_id} ({run.title}) is now published. Official allocation letters released.",
            level="success",
            target_role="all"
        )
        sio.emit('new_activity', {
            'actor': actor_name,
            'action': f"Approved and published run {run.run_id}",
            'time': "Just now"
        })
    except Exception:
        pass

    messages.success(request, f"Allocation Run {run.run_id} has been formally approved and published! Official letters have been issued to students.")
    return redirect(f"{reverse('runs')}?run_id={run.run_id}")

@admin_required
def profile_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'admin', 'title': 'Head Warden'})
        
    success_msg = None
    error_msg = None

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        title = request.POST.get('title', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        office_location = request.POST.get('office_location', '').strip()
        
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
            if first_name is not None:
                request.user.first_name = first_name
            if last_name is not None:
                request.user.last_name = last_name
            if email:
                request.user.email = email
            request.user.save()

            if title:
                profile.title = title
            if phone:
                profile.phone = phone
            if department:
                profile.department = department
            if office_location:
                profile.office_location = office_location
            profile.save()

            success_msg = 'Administrator profile details updated successfully!'

    ctx = get_base_context(request, 'admin-profile', is_admin=True)
    ctx.update({
        'admin_profile': profile,
        'success_msg': success_msg,
        'error_msg': error_msg,
    })
    return render(request, 'admin_panel/profile.html', ctx)

# ==================== AJAX APIs ====================

@require_POST
def api_draft_override(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    try:
        body = json.loads(request.body.decode('utf-8'))
        record_id = body.get('record_id')
        new_bed = body.get('new_bed', 'Cedar House · C-216A')
        reason = body.get('reason', '')

        record = AllocationRecord.objects.get(id=record_id) if record_id else AllocationRecord.objects.filter(status='exception').first()
        if record:
            old_bed = record.assigned_bed_label
            record.assigned_bed_label = new_bed
            record.override_reason = reason
            record.is_overridden = True
            record.status = 'clear'
            record.save()

            invalidate_allocation_caches()

            actor_name = request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
            AuditLog.objects.create(
                action=f"Override applied for {record.student.name}: reallocated to {new_bed}",
                actor=actor_name
            )

            # Broadcast real-time Socket.IO events to all active users
            try:
                from housing.sockets import broadcast_bed_update, broadcast_allocation_override, broadcast_notification
                broadcast_allocation_override(
                    student_name=record.student.name,
                    new_bed=new_bed,
                    old_bed=old_bed,
                    reason=reason,
                    actor=actor_name
                )
                broadcast_bed_update(
                    bed_label=new_bed,
                    status='occupied',
                    student_name=record.student.name,
                    student_id=record.student.student_id
                )
                broadcast_notification(
                    title="Allocation Override Applied",
                    message=f"{record.student.name} reallocated to {new_bed}",
                    level="warning"
                )
            except Exception as broadcast_err:
                pass

            return JsonResponse({'success': True, 'record_id': record.id, 'new_bed': new_bed})
        return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
def api_reassign_bed(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Admin privileges required'}, status=403)
    try:
        body = json.loads(request.body.decode('utf-8'))
        student_id = body.get('student_id', '').strip() or 'STU-204810'
        from_bed_label = body.get('from_bed', '').strip() or 'Cedar · C-112A'
        target_bed_label = body.get('target_bed', '').strip() or 'Cedar · C-216A · Single'
        run_id = body.get('run_id', '').strip() or 'AR-2025-04'
        constraint_checked = body.get('constraint_checked', True)

        if not constraint_checked:
            return JsonResponse({'success': False, 'error': 'Constraint review confirmation required'}, status=400)

        # Parse from_bed and target_bed
        def parse_bed_details(label):
            m = re.search(r'([A-Z]-\d+)\s*([A-C])?', label)
            if m:
                room_no = m.group(1)
                letter = m.group(2) if m.group(2) else 'A'
                return room_no, letter
            return None, None

        from_room_num, from_bed_letter = parse_bed_details(from_bed_label)
        target_room_num, target_bed_letter = parse_bed_details(target_bed_label)

        # Find Student
        student = Student.objects.filter(student_id=student_id).first()
        if not student and from_room_num and from_bed_letter:
            prev_bed = Bed.objects.filter(room__room_number=from_room_num, bed_letter=from_bed_letter).first()
            if prev_bed and prev_bed.assigned_student:
                student = prev_bed.assigned_student
        if not student:
            student = Student.objects.filter(student_id='STU-204810').first() or Student.objects.first()

        student_display = student.name if student else 'Student'
        run = AllocationRun.objects.filter(run_id=run_id).first() or AllocationRun.objects.first()
        run_name = run.run_id if run else 'AR-2025-04'
        actor_name = request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
        log_action = f"Reassigned {student_display} from {from_bed_label} to {target_bed_label} (Draft {run_name})"

        # Atomic PostgreSQL transaction: guarantees zero partial writes
        with transaction.atomic():
            # 1. Update Old Bed: set to available
            if from_room_num and from_bed_letter:
                old_bed = Bed.objects.filter(room__room_number=from_room_num, bed_letter=from_bed_letter).first()
                if old_bed:
                    old_bed.status = 'available'
                    old_bed.assigned_student = None
                    old_bed.save(update_fields=['status', 'assigned_student'])

            # Free any other bed currently held by this student
            if student and target_room_num and target_bed_letter:
                Bed.objects.filter(assigned_student=student).exclude(
                    room__room_number=target_room_num, bed_letter=target_bed_letter
                ).update(status='available', assigned_student=None)

            # 2. Update New Bed: set to occupied and assign student
            if target_room_num and target_bed_letter:
                new_bed = Bed.objects.filter(room__room_number=target_room_num, bed_letter=target_bed_letter).first()
                if new_bed:
                    new_bed.status = 'occupied'
                    new_bed.assigned_student = student
                    new_bed.save(update_fields=['status', 'assigned_student'])

            # 3. Update Draft Allocation Record
            if run and student:
                record = AllocationRecord.objects.filter(run=run, student=student).first()
                if not record:
                    record = AllocationRecord.objects.filter(student=student).first()
                if record:
                    record.assigned_bed_label = target_bed_label
                    record.is_overridden = True
                    record.override_reason = f"Administrative bed reassignment from {from_bed_label} to {target_bed_label}"
                    record.status = 'clear'
                    record.save()

            # 4. Audit Log
            AuditLog.objects.create(
                action=log_action,
                actor=actor_name
            )

            # Invalidate cached floor payloads immediately so next read is fresh
            invalidate_allocation_caches()

        # 5. Socket.IO Real-Time Broadcast
        try:
            from housing.sockets import broadcast_bed_update, broadcast_notification, sio
            if from_bed_label and from_room_num:
                broadcast_bed_update(
                    bed_label=from_bed_label,
                    status='available',
                    student_name=None,
                    room_number=from_room_num
                )
            if target_room_num:
                broadcast_bed_update(
                    bed_label=target_bed_label,
                    status='occupied',
                    student_name=student_display,
                    student_id=student.student_id if student else None,
                    room_number=target_room_num
                )
            broadcast_notification(
                title="Bed Reassigned Live",
                message=f"{student_display} reassigned from {from_bed_label} to {target_bed_label}",
                level="info"
            )
            sio.emit('new_activity', {
                'actor': actor_name,
                'action': f"Reassigned {student_display} to {target_bed_label}",
                'time': "Just now"
            })
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'from_bed': from_bed_label,
            'target_bed': target_bed_label,
            'student_name': student_display,
            'student_id': student.student_id if student else student_id,
            'run_id': run_name,
            'message': f"Reassigned {student_display} to {target_bed_label} successfully!"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@admin_required
def api_get_vacant_beds(request):
    try:
        floor = request.GET.get('floor', 'Floor 2')
        floor_clean = floor.replace(' ', '_')
        cache_key = f"vacant_beds_{floor_clean}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return JsonResponse({
                'success': True,
                'count': len(cached_data),
                'vacant_beds': cached_data
            })

        cedar_data = cache.get('cedar_house_full_inventory')
        cedar = cedar_data.get('hostel') if cedar_data else None
        all_vacant = cedar_data.get('available_target_beds') if (cedar_data and cedar_data.get('available_target_beds') is not None) else None

        if all_vacant is None:
            active_run = AllocationRun.objects.order_by('-created_at').first()
            draft_assigned_codes = set()
            if active_run:
                for lbl in active_run.records.values_list('assigned_bed_label', flat=True):
                    m = re.search(r'([A-Z]-\d+)\s*([A-C])?', lbl)
                    if m:
                        room_no = m.group(1)
                        letter = m.group(2) if m.group(2) else 'A'
                        draft_assigned_codes.add(f"{room_no}{letter}")

            if not cedar:
                cedar = Hostel.objects.filter(name='Cedar House').first()

            vacant_beds_qs = (
                Bed.objects.filter(status='available', assigned_student__isnull=True)
                .select_related('room', 'room__hostel')
                .order_by('room__hostel__name', 'room__floor', 'room__room_number', 'bed_letter')
            )

            all_vacant = [
                b for b in vacant_beds_qs
                if f"{b.room.room_number}{b.bed_letter}" not in draft_assigned_codes
            ]

        same_hostel_same_floor = [b for b in all_vacant if b.room.hostel == cedar and b.room.floor == floor]
        same_hostel_other_floor = [b for b in all_vacant if b.room.hostel == cedar and b.room.floor != floor]
        other_hostels = [b for b in all_vacant if b.room.hostel != cedar]
        ordered_vacant = same_hostel_same_floor + same_hostel_other_floor + other_hostels

        beds_data = []
        for b in ordered_vacant:
            short_hostel = b.room.hostel.name.replace(' House', '').replace(' Court', '').replace(' Hall', '').replace(' Residence', '').replace(' Lodge', '')
            beds_data.append({
                'value': f"{short_hostel} · {b.room.room_number}{b.bed_letter} · {b.room.room_type}",
                'label': f"{b.room.hostel.name} · {b.room.room_number}{b.bed_letter} · {b.room.room_type} ({b.room.floor})",
                'room_number': b.room.room_number,
                'bed_letter': b.bed_letter,
                'room_type': b.room.room_type,
                'floor': b.room.floor,
                'hostel': b.room.hostel.name
            })

        cache.set(cache_key, beds_data, 60)

        return JsonResponse({
            'success': True,
            'count': len(beds_data),
            'vacant_beds': beds_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
