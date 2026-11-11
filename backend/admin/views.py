from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
import json

from housing.models import (
    Hostel, Student, Room, Bed, AllocationRun, AllocationRecord,
    AuditLog, UserProfile
)
from housing.decorators import admin_required
from housing.views import get_base_context

@admin_required
def admin_overview(request):
    ctx = get_base_context(request, 'admin-overview', is_admin=True)
    hostels = Hostel.objects.all()
    total_beds = sum(h.total_beds for h in hostels) or 2480
    available_beds = sum(h.beds_available for h in hostels) or 654
    occupied_beds = total_beds - available_beds
    occupancy_pct = round((occupied_beds / total_beds) * 100, 1) if total_beds else 73.6

    ctx.update({
        'hostels': hostels,
        'total_beds': f"{total_beds:,}",
        'occupied_beds': f"{occupied_beds:,}",
        'available_beds': f"{available_beds:,}",
        'occupancy_pct': occupancy_pct,
        'applications_count': '2,104',
        'pending_review': 36,
        'recent_logs': AuditLog.objects.all()[:4],
    })
    return render(request, 'admin_panel/admin_overview.html', ctx)

@admin_required
def bedmap_view(request):
    floor = request.GET.get('floor', 'Floor 2')
    cedar = Hostel.objects.filter(name='Cedar House').first()
    rooms = Room.objects.filter(hostel=cedar, floor=floor).prefetch_related('beds') if cedar else []

    ctx = get_base_context(request, 'bedmap', is_admin=True)
    ctx.update({
        'hostel': cedar,
        'floor': floor,
        'rooms': rooms,
        'total_beds': 60,
        'available_count': 18,
        'occupied_count': 42,
        'reserved_count': 5,
        'accessible_count': 4,
    })
    return render(request, 'admin_panel/bedmap.html', ctx)

@admin_required
def draft_review(request):
    run = AllocationRun.objects.first()
    filter_status = request.GET.get('filter', 'all')
    search = request.GET.get('q', '').strip()

    records_qs = AllocationRecord.objects.select_related('student', 'run')
    if run:
        records_qs = records_qs.filter(run=run)

    if filter_status in ['clear', 'exception']:
        records_qs = records_qs.filter(status=filter_status)

    if search:
        records_qs = records_qs.filter(student__name__icontains=search)

    ctx = get_base_context(request, 'draft', is_admin=True)
    ctx.update({
        'run': run,
        'records': records_qs,
        'filter_status': filter_status,
        'search_query': search,
    })
    return render(request, 'admin_panel/draft_review.html', ctx)

@admin_required
def runs_view(request):
    run = AllocationRun.objects.first()
    ctx = get_base_context(request, 'runs', is_admin=True)
    ctx.update({
        'run': run,
    })
    return render(request, 'admin_panel/runs.html', ctx)

@admin_required
def placeholder_view(request, section):
    ctx = get_base_context(request, section, is_admin=True)
    ctx.update({
        'section_name': section.replace('-', ' ').title(),
    })
    return render(request, 'admin_panel/placeholder.html', ctx)

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
            record.assigned_bed_label = new_bed
            record.override_reason = reason
            record.is_overridden = True
            record.status = 'clear'
            record.save()

            AuditLog.objects.create(
                action=f"Override applied for {record.student.name}: reallocated to {new_bed}",
                actor=request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
            )
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
        student_id = body.get('student_id', 'STU-204810')
        target_bed_label = body.get('target_bed', 'C-216A')

        student = Student.objects.filter(student_id=student_id).first()
        AuditLog.objects.create(
            action=f"Reassigned {student.name if student else 'Student'} to {target_bed_label} (Draft AR-2025-04)",
            actor=request.user.get_full_name() or request.user.username or 'Dr. Sarah Moore'
        )
        return JsonResponse({'success': True, 'target_bed': target_bed_label})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
