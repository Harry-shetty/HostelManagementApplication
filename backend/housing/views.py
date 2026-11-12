from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from .models import (
    Student, Notification
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


def get_mock_applications(filter_val=None, search_query=None):
    items = [
        {
            'id': 'NST-25-10482',
            'student_name': 'Amara Mensah',
            'student_id': 'STU-204810',
            'programme': 'Computer Science & AI · Year 2',
            'first_preference': 'Cedar House',
            'second_preference': 'Maple Court',
            'room_type': 'Single room',
            'quota': 'Continuing Students',
            'status': 'Verified',
            'submitted_at': '6 Oct 2025, 14:20',
            'avatar_initials': 'AM',
            'avatar_color': 'green',
            'notes': 'Requested quiet study environment near Computer Science faculty.'
        },
        {
            'id': 'NST-25-10483',
            'student_name': 'Maya Okafor',
            'student_id': 'STU-204746',
            'programme': 'Architecture · Year 2',
            'first_preference': 'Maple Court',
            'second_preference': 'Cedar House',
            'room_type': 'Ensuite room',
            'quota': 'Continuing Students',
            'status': 'Verified',
            'submitted_at': '6 Oct 2025, 15:45',
            'avatar_initials': 'MO',
            'avatar_color': 'peach',
            'notes': 'Proximity to Architecture design studio drafting workshops required.'
        },
        {
            'id': 'NST-25-10484',
            'student_name': 'Daniel Kim',
            'student_id': 'STU-204612',
            'programme': 'Mechanical Engineering · Year 1',
            'first_preference': 'Willow Hall',
            'second_preference': 'Cedar House',
            'room_type': 'Ground floor accessible',
            'quota': 'Special Accommodations',
            'status': 'Under Review',
            'submitted_at': '7 Oct 2025, 09:12',
            'avatar_initials': 'DK',
            'avatar_color': 'green',
            'notes': 'Medical ground-floor mobility accommodation with step-free bathroom access.'
        },
        {
            'id': 'NST-25-10485',
            'student_name': 'Leila Chen',
            'student_id': 'STU-204588',
            'programme': 'Economics · Year 3',
            'first_preference': 'Cedar House',
            'second_preference': 'Oak Residence',
            'room_type': 'Single room',
            'quota': 'Continuing Students',
            'status': 'Allocated',
            'submitted_at': '5 Oct 2025, 18:30',
            'avatar_initials': 'LC',
            'avatar_color': 'blue',
            'notes': 'Final-year research scholar dissertation quiet period requested.'
        },
        {
            'id': 'NST-25-10486',
            'student_name': 'Jon Bell',
            'student_id': 'STU-204490',
            'programme': 'Business Analytics · Year 2',
            'first_preference': 'Pine Lodge',
            'second_preference': 'Willow Hall',
            'room_type': 'Twin room',
            'quota': 'Continuing Students',
            'status': 'Waitlisted',
            'submitted_at': '8 Oct 2025, 11:05',
            'avatar_initials': 'JB',
            'avatar_color': 'gray',
            'notes': 'Applied for general undergraduate ballot. Currently queued in waitlist Tier 2.'
        },
        {
            'id': 'NST-25-10487',
            'student_name': 'Zara Bello',
            'student_id': 'STU-204512',
            'programme': 'Medicine · Year 2',
            'first_preference': 'Pine Lodge',
            'second_preference': 'Cedar House',
            'room_type': 'Single room',
            'quota': 'Continuing Students',
            'status': 'Verified',
            'submitted_at': '6 Oct 2025, 12:15',
            'avatar_initials': 'ZB',
            'avatar_color': 'purple',
            'notes': 'Hospital clinical rotation early shift schedule.'
        },
        {
            'id': 'NST-25-10488',
            'student_name': 'Rohan Sharma',
            'student_id': 'STU-204921',
            'programme': 'Data Science · Year 1',
            'first_preference': 'Maple Court',
            'second_preference': 'Cedar House',
            'room_type': 'Ensuite room',
            'quota': 'First-Year Freshers',
            'status': 'Verified',
            'submitted_at': '9 Oct 2025, 08:40',
            'avatar_initials': 'RS',
            'avatar_color': 'blue',
            'notes': 'Guaranteed freshers quota accommodation applicant.'
        },
        {
            'id': 'NST-25-10489',
            'student_name': 'Elena Rostova',
            'student_id': 'STU-204935',
            'programme': 'Biomedical Sciences (MSc) · Year 1',
            'first_preference': 'Oak Residence',
            'second_preference': 'Maple Court',
            'room_type': 'Studio room',
            'quota': 'Postgraduates',
            'status': 'Under Review',
            'submitted_at': '9 Oct 2025, 16:22',
            'avatar_initials': 'ER',
            'avatar_color': 'peach',
            'notes': 'Postgraduate research scholar requiring year-round tenancy.'
        },
        {
            'id': 'NST-25-10490',
            'student_name': 'Kwame Mensah',
            'student_id': 'STU-204950',
            'programme': 'Civil Engineering · Year 1',
            'first_preference': 'Willow Hall',
            'second_preference': 'Pine Lodge',
            'room_type': 'Twin room',
            'quota': 'International',
            'status': 'Action Required',
            'submitted_at': '10 Oct 2025, 13:10',
            'avatar_initials': 'KM',
            'avatar_color': 'green',
            'notes': 'International scholarship passport / visa verification documents pending review.'
        },
        {
            'id': 'NST-25-10491',
            'student_name': 'Sophie Dubois',
            'student_id': 'STU-204962',
            'programme': 'International Relations · Year 1',
            'first_preference': 'Cedar House',
            'second_preference': 'Willow Hall',
            'room_type': 'Twin room',
            'quota': 'First-Year Freshers',
            'status': 'Verified',
            'submitted_at': '10 Oct 2025, 15:50',
            'avatar_initials': 'SD',
            'avatar_color': 'purple',
            'notes': 'Standard first-year undergraduate allocation.'
        }
    ]

    if filter_val == 'under_review':
        items = [i for i in items if i['status'] in ('Under Review', 'Action Required')]
    elif filter_val == 'verified':
        items = [i for i in items if i['status'] in ('Verified', 'Allocated')]
    elif filter_val == 'special':
        items = [i for i in items if i['quota'] == 'Special Accommodations']

    if search_query:
        sq = search_query.lower()
        items = [
            i for i in items if (
                sq in i['student_name'].lower() or
                sq in i['student_id'].lower() or
                sq in i['id'].lower() or
                sq in i['programme'].lower()
            )
        ]
    return items


def get_mock_waitlist(filter_val=None, search_query=None):
    items = [
        {
            'position': 1,
            'student_name': 'Daniel Kim',
            'student_id': 'STU-204612',
            'programme': 'Mechanical Engineering · Year 1',
            'tier': 'Tier 1 · Medical / Hardship',
            'preferred_hostel': 'Willow Hall or Cedar House (Accessible)',
            'room_type': 'Ground Floor Single',
            'date_queued': '6 Oct 2025',
            'status': 'Offer Pending',
            'expiration': 'Expires in 14h (Willow W-102A)',
            'avatar_initials': 'DK',
            'avatar_color': 'green'
        },
        {
            'position': 2,
            'student_name': 'Fatima Al-Hassan',
            'student_id': 'STU-204988',
            'programme': 'Biomedical Science · Year 1',
            'tier': 'Tier 1 · Medical / Hardship',
            'preferred_hostel': 'Cedar House · Any Single',
            'room_type': 'Single room',
            'date_queued': '6 Oct 2025',
            'status': 'Offer Pending',
            'expiration': 'Expires in 26h (Cedar C-114A)',
            'avatar_initials': 'FA',
            'avatar_color': 'peach'
        },
        {
            'position': 3,
            'student_name': 'Jon Bell',
            'student_id': 'STU-204490',
            'programme': 'Business Analytics · Year 2',
            'tier': 'Tier 2 · Distance Priority',
            'preferred_hostel': 'Pine Lodge or Willow Hall',
            'room_type': 'Twin room',
            'date_queued': '7 Oct 2025',
            'status': 'Next in Line',
            'expiration': None,
            'avatar_initials': 'JB',
            'avatar_color': 'gray'
        },
        {
            'position': 4,
            'student_name': 'Tariq Mansoor',
            'student_id': 'STU-204991',
            'programme': 'Computer Science · Year 1',
            'tier': 'Tier 2 · Distance Priority',
            'preferred_hostel': 'Maple Court · Ensuite',
            'room_type': 'Ensuite room',
            'date_queued': '7 Oct 2025',
            'status': 'Queued (#4)',
            'expiration': None,
            'avatar_initials': 'TM',
            'avatar_color': 'blue'
        },
        {
            'position': 5,
            'student_name': 'Chun-Kit Wong',
            'student_id': 'STU-204994',
            'programme': 'Electrical Engineering · Year 1',
            'tier': 'Tier 2 · Distance Priority',
            'preferred_hostel': 'Cedar House · Single',
            'room_type': 'Single room',
            'date_queued': '8 Oct 2025',
            'status': 'Queued (#5)',
            'expiration': None,
            'avatar_initials': 'CW',
            'avatar_color': 'purple'
        },
        {
            'position': 6,
            'student_name': 'Amina Yusuf',
            'student_id': 'STU-204997',
            'programme': 'Law (LLB) · Year 1',
            'tier': 'Tier 3 · General Ballot',
            'preferred_hostel': 'Any Available Twin Room',
            'room_type': 'Twin room',
            'date_queued': '8 Oct 2025',
            'status': 'Queued (#6)',
            'expiration': None,
            'avatar_initials': 'AY',
            'avatar_color': 'green'
        },
        {
            'position': 7,
            'student_name': 'Lucas Morales',
            'student_id': 'STU-205001',
            'programme': 'Physics · Year 2',
            'tier': 'Tier 3 · General Ballot',
            'preferred_hostel': 'Oak Residence · Studio',
            'room_type': 'Studio room',
            'date_queued': '8 Oct 2025',
            'status': 'Queued (#7)',
            'expiration': None,
            'avatar_initials': 'LM',
            'avatar_color': 'peach'
        },
        {
            'position': 8,
            'student_name': 'Grace O\'Connor',
            'student_id': 'STU-205005',
            'programme': 'English Literature · Year 1',
            'tier': 'Tier 3 · General Ballot',
            'preferred_hostel': 'Cedar House · Twin',
            'room_type': 'Twin room',
            'date_queued': '9 Oct 2025',
            'status': 'Queued (#8)',
            'expiration': None,
            'avatar_initials': 'GO',
            'avatar_color': 'blue'
        }
    ]

    if filter_val == 'tier1':
        items = [i for i in items if 'Tier 1' in i['tier']]
    elif filter_val == 'pending':
        items = [i for i in items if i['status'] == 'Offer Pending']
    elif filter_val == 'placed':
        items = [i for i in items if i['status'] == 'Placed']

    if search_query:
        sq = search_query.lower()
        items = [
            i for i in items if (
                sq in i['student_name'].lower() or
                sq in i['student_id'].lower() or
                sq in str(i['position']) or
                sq in i['programme'].lower()
            )
        ]
    return items
