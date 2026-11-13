import hashlib
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from housing.models import (
    Hostel, Student, Room, Bed, AllocationCycle, EligibilityRule,
    Application, ApplicationPreference, RoommateProfile, RoommateSuggestion,
    AllocationRun, AllocationRecord, AllocationApproval, AllocationLetter,
    RoomChangeRequest, WaitlistEntry, AuditLog, Notification, UserProfile
)

PHOTOS = {
    'cedar': 'https://images.unsplash.com/photo-1753764403695-f43eb7cbead4?auto=format&fit=crop&w=1200&q=85',
    'maple': 'https://images.unsplash.com/photo-1596276020587-8044fe049813?auto=format&fit=crop&w=1200&q=85',
    'willow': 'https://images.unsplash.com/photo-1709949908229-53f3898aceab?auto=format&fit=crop&w=1200&q=85',
    'oak': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=85',
    'pine': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=85',
}

def make_digest(action: str, actor: str, ts_str: str) -> str:
    raw = f"{action}|{actor}|{ts_str}|nestora-gov-v3"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

class Command(BaseCommand):
    help = 'Seeds initial data for the Nestora student housing system honoring P03 specification'

    def handle(self, *args, **options):
        self.stdout.write("Seeding structured Nestora housing data in PostgreSQL...")

        now = timezone.now()

        # 0. Clean old records cleanly in dependency order
        WaitlistEntry.objects.all().delete()
        RoomChangeRequest.objects.all().delete()
        AllocationLetter.objects.all().delete()
        AllocationApproval.objects.all().delete()
        AllocationRecord.objects.all().delete()
        AllocationRun.objects.all().delete()
        ApplicationPreference.objects.all().delete()
        Application.objects.all().delete()
        EligibilityRule.objects.all().delete()
        AllocationCycle.objects.all().delete()
        RoommateSuggestion.objects.all().delete()
        RoommateProfile.objects.all().delete()
        Bed.objects.all().delete()
        Room.objects.all().delete()
        Hostel.objects.all().delete()
        Student.objects.all().delete()
        AuditLog.objects.all().delete()
        Notification.objects.all().delete()

        # 1. Allocation Cycles (M2)
        cycle_main = AllocationCycle.objects.create(
            cycle_id='CYC-2025-26',
            title='Academic Year 2025/26 Main Intake',
            academic_year='2025/26',
            window_open=now - timedelta(days=60),
            window_close=now - timedelta(days=10),
            status='review',
            is_active=True,
            description='Primary autumn residential allocation cycle across all university halls.',
            quota_distribution={
                'First-Year Freshers': 40,
                'Continuing Students': 35,
                'International Students': 15,
                'Special Accommodations': 10
            }
        )

        cycle_spring = AllocationCycle.objects.create(
            cycle_id='CYC-2025-SP',
            title='Spring 2026 Supplementary Intake',
            academic_year='2025/26',
            window_open=now + timedelta(days=15),
            window_close=now + timedelta(days=45),
            status='open',
            is_active=False,
            description='Supplementary semester 2 exchange and postgraduate intake.',
            quota_distribution={
                'First-Year Freshers': 20,
                'Continuing Students': 40,
                'International Students': 30,
                'Special Accommodations': 10
            }
        )

        # 2. Eligibility & Policy Rules (M3)
        rules = [
            EligibilityRule(
                code='ELIG-ACAD-GOOD',
                name='Good Academic Standing',
                category='Academic',
                description='Applicant must maintain a minimum cumulative GPA >= 2.0 with no active academic probation.',
                is_mandatory=True,
                is_active=True
            ),
            EligibilityRule(
                code='ELIG-DIST-50',
                name='Distance Threshold (>50 km)',
                category='Geographic',
                description='Permanent home domicile must be located more than 50 kilometers from the central campus boundary.',
                is_mandatory=True,
                is_active=True
            ),
            EligibilityRule(
                code='ELIG-FEE-CLEAR',
                name='Financial Services Fee Clearance',
                category='Financial',
                description='Student account must have zero overdue tuition balances or prior residential hall debt.',
                is_mandatory=True,
                is_active=True
            ),
            EligibilityRule(
                code='ELIG-DISC-CLEAN',
                name='Disciplinary & Conduct Compliance',
                category='Conduct',
                description='Applicant must have no active sanctions under university disciplinary ordinances.',
                is_mandatory=True,
                is_active=True
            ),
            EligibilityRule(
                code='ELIG-MED-VERIF',
                name='Medical / Disability Accommodations Endorsement',
                category='Special Accommodations',
                description='Ground-floor or step-free access requirements must be certified by University Health & Wellbeing.',
                is_mandatory=False,
                is_active=True
            ),
        ]
        EligibilityRule.objects.bulk_create(rules)

        # 3. Hostels (M1)
        cedar = Hostel.objects.create(
            name='Cedar House',
            slug='cedar-house',
            location='North Campus · 4 min walk',
            price_per_semester=18500,
            beds_available=18,
            total_beds=60,
            occupancy_percent=88,
            image_url=PHOTOS['cedar'],
            room_summary='Single & twin rooms',
            tags=['Wi-Fi', 'Study rooms', 'Laundry']
        )
        maple = Hostel.objects.create(
            name='Maple Court',
            slug='maple-court',
            location='Central Campus · 2 min walk',
            price_per_semester=20500,
            beds_available=11,
            total_beds=55,
            occupancy_percent=79,
            image_url=PHOTOS['maple'],
            room_summary='Ensuite rooms',
            tags=['Gym', 'Courtyard', 'Kitchen']
        )
        willow = Hostel.objects.create(
            name='Willow Hall',
            slug='willow-hall',
            location='East Campus · 5 min walk',
            price_per_semester=16500,
            beds_available=26,
            total_beds=70,
            occupancy_percent=74,
            image_url=PHOTOS['willow'],
            room_summary='Twin & triple rooms',
            tags=['Accessible', 'Library', 'Café']
        )
        oak = Hostel.objects.create(
            name='Oak Residence',
            slug='oak-residence',
            location='West Campus · 8 min walk',
            price_per_semester=17500,
            beds_available=15,
            total_beds=50,
            occupancy_percent=68,
            image_url=PHOTOS['oak'],
            room_summary='Studio & single rooms',
            tags=['Quiet zone', 'Bicycle storage', 'Balcony']
        )
        pine = Hostel.objects.create(
            name='Pine Lodge',
            slug='pine-lodge',
            location='South Campus · 10 min walk',
            price_per_semester=15500,
            beds_available=20,
            total_beds=45,
            occupancy_percent=56,
            image_url=PHOTOS['pine'],
            room_summary='Shared apartments',
            tags=['Garden', 'Games room', 'Dining hall']
        )

        # 4. Students
        amara = Student.objects.create(
            name='Amara Mensah',
            student_id='STU-204810',
            email='amara.m@university.edu',
            programme='Computer Science & AI',
            year='Year 2',
            avatar_initials='AM',
            avatar_color='green',
            phone='+44 7700 900142',
            emergency_contact='Kofi Mensah · +44 7700 900981 (Parent)',
            bio='Second-year CS student interested in software engineering. Quiet during weeknights, prefer clean and friendly shared living.',
            eligibility_status='Verified'
        )
        maya = Student.objects.create(
            name='Maya Okafor',
            student_id='STU-204746',
            email='maya.o@university.edu',
            programme='Architecture',
            year='Year 2',
            avatar_initials='MO',
            avatar_color='peach',
            phone='+44 7700 900253',
            emergency_contact='Grace Okafor · +44 7700 900812 (Parent)',
            bio='Architecture student working on studio projects. Values tidy work areas and early morning sketching.',
            eligibility_status='Verified'
        )
        daniel = Student.objects.create(
            name='Daniel Kim',
            student_id='STU-204612',
            email='daniel.k@university.edu',
            programme='Mechanical Engineering',
            year='Year 1',
            avatar_initials='DK',
            avatar_color='green',
            phone='+44 7700 900384',
            emergency_contact='Min-Soo Kim · +44 7700 900741 (Parent)',
            bio='First-year engineering fresher with certified mobility restriction. Requires ground-floor wheelchair accessibility.',
            eligibility_status='Review'
        )
        leila = Student.objects.create(
            name='Leila Chen',
            student_id='STU-204588',
            email='leila.c@university.edu',
            programme='Economics',
            year='Year 3',
            avatar_initials='LC',
            avatar_color='blue',
            phone='+44 7700 900495',
            emergency_contact='David Chen · +44 7700 900673 (Parent)',
            bio='Final-year economics honours student preparing dissertation. Early sleeper and library regular.',
            eligibility_status='Verified'
        )
        jon = Student.objects.create(
            name='Jon Bell',
            student_id='STU-204490',
            email='jon.b@university.edu',
            programme='Business Analytics',
            year='Year 2',
            avatar_initials='JB',
            avatar_color='peach',
            phone='+44 7700 900516',
            emergency_contact='Sarah Bell · +44 7700 900598 (Parent)',
            bio='Second-year business student. Active in campus rowing club and friendly living environment.',
            eligibility_status='Verified'
        )
        zara = Student.objects.create(
            name='Zara Bello',
            student_id='STU-204512',
            email='zara.b@university.edu',
            programme='Medicine',
            year='Year 2',
            avatar_initials='ZB',
            avatar_color='purple',
            phone='+44 7700 900627',
            emergency_contact='Ibrahim Bello · +44 7700 900421 (Parent)',
            bio='Medical student with hospital clinical rotations starting at 7 AM. Very quiet during evening hours.',
            eligibility_status='Verified'
        )
        tariq = Student.objects.create(
            name='Tariq Mansoor',
            student_id='STU-204991',
            email='tariq.m@university.edu',
            programme='Computer Science',
            year='Year 1',
            avatar_initials='TM',
            avatar_color='blue',
            phone='+44 7700 900738',
            emergency_contact='Nasir Mansoor · +44 7700 900352 (Parent)',
            bio='First-year CS fresher keen on robotics and AI competitions.',
            eligibility_status='Verified'
        )
        fatima = Student.objects.create(
            name='Fatima Al-Hassan',
            student_id='STU-204988',
            email='fatima.a@university.edu',
            programme='Biomedical Science',
            year='Year 1',
            avatar_initials='FA',
            avatar_color='peach',
            phone='+44 7700 900849',
            emergency_contact='Zainab Al-Hassan · +44 7700 900261 (Parent)',
            bio='First-year biomedical science student with registered medical accommodation.',
            eligibility_status='Verified'
        )
        rohan = Student.objects.create(
            name='Rohan Sharma',
            student_id='STU-204921',
            email='rohan.s@university.edu',
            programme='Data Science',
            year='Year 1',
            avatar_initials='RS',
            avatar_color='blue',
            phone='+44 7700 900950',
            emergency_contact='Anita Sharma · +44 7700 900174 (Parent)',
            bio='Data science fresher under guaranteed freshers residential quota.',
            eligibility_status='Verified'
        )
        elena = Student.objects.create(
            name='Elena Rostova',
            student_id='STU-204935',
            email='elena.r@university.edu',
            programme='Biomedical Sciences (MSc)',
            year='Postgraduate',
            avatar_initials='ER',
            avatar_color='peach',
            phone='+44 7700 900162',
            emergency_contact='Viktor Rostov · +44 7700 900985 (Parent)',
            bio='Postgraduate laboratory researcher needing year-round quiet accommodation.',
            eligibility_status='Review'
        )
        kwame = Student.objects.create(
            name='Kwame Mensah',
            student_id='STU-204950',
            email='kwame.m@university.edu',
            programme='Civil Engineering',
            year='Year 1',
            avatar_initials='KM',
            avatar_color='green',
            phone='+44 7700 900273',
            emergency_contact='Akua Mensah · +44 7700 900896 (Parent)',
            bio='International scholarship scholar. Visa documentation in final verification.',
            eligibility_status='Review'
        )
        sophie = Student.objects.create(
            name='Sophie Dubois',
            student_id='STU-204962',
            email='sophie.d@university.edu',
            programme='International Relations',
            year='Year 1',
            avatar_initials='SD',
            avatar_color='purple',
            phone='+44 7700 900384',
            emergency_contact='Claire Dubois · +44 7700 900707 (Parent)',
            bio='First-year international relations student active in Model UN.',
            eligibility_status='Verified'
        )

        # 5. Inventory: Rooms and Beds (M1)
        # Cedar House: Floors 1, 2, 3
        for floor_num in [1, 2, 3]:
            floor_name = f"Floor {floor_num}"
            for idx in range(1, 17):
                room_num = f"C-{floor_num}{idx:02d}"
                is_single = (idx % 4 == 0)
                is_accessible = (idx % 5 == 0)
                r_type = 'Single' if is_single else 'Twin'

                room = Room.objects.create(
                    hostel=cedar,
                    room_number=room_num,
                    floor=floor_name,
                    wing='North wing',
                    gender='Female' if idx % 2 == 0 else 'Male',
                    access_type='Accessible' if is_accessible else 'Standard',
                    room_type=r_type
                )

                # Bed A
                assigned_a = None
                if room_num == 'C-214':
                    assigned_a = amara
                elif room_num == 'C-119':
                    assigned_a = leila
                elif room_num == 'C-114':
                    assigned_a = fatima

                status_a = 'occupied' if assigned_a else ('accessible' if is_accessible else ('occupied' if idx % 3 != 0 else 'available'))
                Bed.objects.create(
                    room=room,
                    bed_letter='A',
                    status=status_a,
                    assigned_student=assigned_a,
                    notes='Draft assigned' if assigned_a else ''
                )

                # Bed B (if twin)
                if not is_single:
                    status_b = 'reserved' if (idx % 7 == 2) else ('available' if idx % 3 == 0 else 'occupied')
                    if room_num == 'C-214':
                        status_b = 'available'
                    Bed.objects.create(
                        room=room,
                        bed_letter='B',
                        status=status_b,
                        assigned_student=None,
                        notes='Standard bed'
                    )

        # Maple Court: 10 ensuite rooms
        for idx in range(1, 11):
            room_num = f"M-1{idx:02d}"
            room = Room.objects.create(
                hostel=maple,
                room_number=room_num,
                floor='Floor 1',
                wing='Courtyard wing',
                gender='Female' if idx % 2 == 0 else 'Male',
                access_type='Standard',
                room_type='Single'
            )
            assigned = maya if room_num == 'M-108' else (tariq if room_num == 'M-102' else None)
            Bed.objects.create(
                room=room,
                bed_letter='A',
                status='occupied' if assigned else 'available',
                assigned_student=assigned,
                notes='Ensuite room assignment' if assigned else ''
            )

        # Willow Hall: 12 rooms (accessible & standard)
        for idx in range(1, 13):
            room_num = f"W-1{idx:02d}" if idx <= 6 else f"W-2{idx-6:02d}"
            floor_name = 'Floor 1' if idx <= 6 else 'Floor 2'
            room = Room.objects.create(
                hostel=willow,
                room_number=room_num,
                floor=floor_name,
                wing='Garden wing',
                gender='Male' if idx % 2 == 0 else 'Female',
                access_type='Accessible' if idx in [1, 2] else 'Standard',
                room_type='Single' if idx in [1, 2] else 'Twin'
            )
            assigned = daniel if room_num == 'W-102' else (sophie if room_num == 'W-201' else None)
            Bed.objects.create(
                room=room,
                bed_letter='A',
                status='occupied' if assigned else 'available',
                assigned_student=assigned,
                notes='Ground floor accessible' if idx in [1, 2] else ''
            )
            if idx > 2:
                Bed.objects.create(
                    room=room,
                    bed_letter='B',
                    status='available',
                    assigned_student=None
                )

        # 6. Applications & Preferences (M2, M4)
        apps_data = [
            (amara, 'NST-25-10482', 'under_review', 60, 3, 'Single room', 'Continuing Students', 'Requested quiet study environment near Computer Science faculty.', [(cedar, 1), (maple, 2), (willow, 3)]),
            (maya, 'NST-25-10483', 'submitted', 100, 4, 'Ensuite room', 'Continuing Students', 'Proximity to Architecture design studio drafting workshops required.', [(maple, 1), (cedar, 2)]),
            (daniel, 'NST-25-10484', 'under_review', 80, 4, 'Ground floor accessible', 'Special Accommodations', 'Medical ground-floor mobility accommodation with step-free bathroom access.', [(willow, 1), (cedar, 2)]),
            (leila, 'NST-25-10485', 'allocated', 100, 4, 'Single room', 'Continuing Students', 'Final-year research scholar dissertation quiet period requested.', [(cedar, 1), (oak, 2)]),
            (jon, 'NST-25-10486', 'waitlisted', 100, 4, 'Twin room', 'Continuing Students', 'Applied for general undergraduate ballot. Currently queued in waitlist Tier 2.', [(pine, 1), (willow, 2)]),
            (zara, 'NST-25-10487', 'submitted', 100, 4, 'Single room', 'Continuing Students', 'Hospital clinical rotation early shift schedule.', [(pine, 1), (cedar, 2)]),
            (rohan, 'NST-25-10488', 'submitted', 100, 4, 'Ensuite room', 'First-Year Freshers', 'Guaranteed freshers quota accommodation applicant.', [(maple, 1), (cedar, 2)]),
            (elena, 'NST-25-10489', 'under_review', 90, 4, 'Studio room', 'Postgraduates', 'Postgraduate research scholar requiring year-round tenancy.', [(oak, 1), (maple, 2)]),
            (kwame, 'NST-25-10490', 'under_review', 70, 3, 'Twin room', 'International', 'International scholarship passport / visa verification documents pending review.', [(willow, 1), (pine, 2)]),
            (sophie, 'NST-25-10491', 'allocated', 100, 4, 'Twin room', 'First-Year Freshers', 'Standard first-year undergraduate allocation.', [(cedar, 1), (willow, 2)]),
        ]

        for s, app_id, st, prog, step, rtype, quota, notes, prefs in apps_data:
            app_obj = Application.objects.create(
                application_id=app_id,
                student=s,
                cycle=cycle_main,
                academic_year='2025/26',
                quota=quota,
                status=st,
                progress_percentage=prog,
                current_step=step,
                room_type_preference=rtype,
                additional_notes=notes,
                created_at=now - timedelta(days=20),
                submitted_at=now - timedelta(days=15)
            )
            for h, rank in prefs:
                ApplicationPreference.objects.create(application=app_obj, hostel=h, rank=rank)

        # 7. Consented Lifestyle Questionnaires & Compatibility (M5)
        RoommateProfile.objects.create(
            student=amara,
            sleep_schedule='10 PM – 12 AM',
            cleanliness='Generally tidy',
            noise_level='Low background noise',
            interests='Computer Science · Web Design · Reading'
        )
        RoommateProfile.objects.create(
            student=maya,
            sleep_schedule='10 PM – 12 AM',
            cleanliness='Very tidy',
            noise_level='Low background noise',
            interests='Architecture · Sketching · Cycling'
        )
        RoommateProfile.objects.create(
            student=leila,
            sleep_schedule='10 PM – 12 AM',
            cleanliness='Generally tidy',
            noise_level='Silent study only',
            interests='Economics · Classical Music · Tennis'
        )
        RoommateProfile.objects.create(
            student=zara,
            sleep_schedule='9 PM – 11 PM',
            cleanliness='Moderately clean',
            noise_level='Low background noise',
            interests='Medicine · Running · Podcasts'
        )

        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=maya,
            compatibility_score=92,
            align_items=['Similar sleep schedule', 'Quiet study time', 'No indoor smoking'],
            difference='Different social pace on weekends',
            is_best_match=True,
            is_saved=False
        )
        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=leila,
            compatibility_score=87,
            align_items=['Both early risers', 'Shared cleaning expectations', 'Weekday focus'],
            difference='Different guest visiting preferences',
            is_best_match=False,
            is_saved=False
        )
        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=zara,
            compatibility_score=84,
            align_items=['Quiet evening hours', 'Similar study focus'],
            difference='Different musical background habits',
            is_best_match=False,
            is_saved=False
        )

        # 8. Allocation Draft Runs & Assignments (M6, M7)
        run_draft = AllocationRun.objects.create(
            run_id='AR-2025-04',
            title='Main Autumn Allocation (Draft v4)',
            status='draft',
            reproducibility_seed='NST-7F3A29',
            allocated_count=1942,
            top_preference_percent=78.4,
            waitlisted_count=162,
            exceptions_count=8,
            validation_status='Passed',
            created_at=now - timedelta(days=2)
        )

        draft_records = [
            (amara, 'Cedar · C-214A', '1st choice', 'Verified', 'clear', 'Matched 1st preference; accessibility & quota satisfied.', None, False),
            (maya, 'Maple · M-108B', '2nd choice', 'Verified', 'clear', 'Matched 2nd preference; Architecture faculty proximity satisfied.', None, False),
            (daniel, 'Willow · W-302A', '3rd choice', 'Review', 'exception', 'Assigned floor 3 but requires ground-floor step-free access per medical certificate.', 'Warden flagged: reassign to ground floor W-102A immediately.', True),
            (leila, 'Cedar · C-119A', '1st choice', 'Verified', 'clear', 'Matched 1st preference; research quiet floor criteria satisfied.', None, False),
            (jon, 'Pine · P-204B', 'Outside top 3', 'Verified', 'exception', 'Cedar and Willow full at quota capacity; placed in fallback hall.', 'Warden exception logged: eligible for priority waitlist Tier 2.', True),
            (tariq, 'Maple · M-102A', '1st choice', 'Verified', 'clear', 'Matched 1st preference ensuite room under freshers quota.', None, False),
            (fatima, 'Cedar · C-114A', '1st choice', 'Verified', 'clear', 'Matched 1st preference single room with verified medical accommodation.', None, False),
            (sophie, 'Willow · W-201A', '2nd choice', 'Verified', 'clear', 'Matched 2nd preference twin room in Willow Hall.', None, False),
        ]

        for s, bed_lbl, pref, elig, st, expl, or_reason, is_or in draft_records:
            AllocationRecord.objects.create(
                run=run_draft,
                student=s,
                assigned_bed_label=bed_lbl,
                preference_matched=pref,
                eligibility_status=elig,
                status=st,
                assignment_explanation=expl,
                override_reason=or_reason,
                is_overridden=is_or
            )

        # Prior Published Run AR-2024-01 to demonstrate draft vs published separation
        run_published = AllocationRun.objects.create(
            run_id='AR-2024-01',
            title='Academic Year 2024/25 Allocation',
            status='published',
            reproducibility_seed='NST-4E1B92',
            allocated_count=1820,
            top_preference_percent=81.2,
            waitlisted_count=140,
            exceptions_count=0,
            validation_status='Passed',
            created_at=now - timedelta(days=365)
        )

        AllocationApproval.objects.create(
            run=run_published,
            approved_by='Dr. Sarah Moore',
            approver_role='Head Warden',
            approval_notes='All quota constraints, medical accommodations, and exceptions verified in compliance with university housing policy v3.2.',
            approved_at=now - timedelta(days=360),
            is_published=True,
            published_at=now - timedelta(days=360),
            digital_signature='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        )

        # 9. Priority Waiting List Entries (M8)
        WaitlistEntry.objects.create(
            student=daniel,
            cycle=cycle_main,
            tier=1,
            tier_label='Tier 1 · Medical / Hardship',
            position=1,
            priority_points=98,
            preferred_hostels='Willow Hall or Cedar House (Accessible)',
            room_type_preference='Ground Floor Single',
            status='offered',
            offer_bed_label='Willow · W-102A',
            offer_expires_at=now + timedelta(hours=14),
            notes='Certified mobility accommodation. Offer extended for accessible ground-floor single.'
        )
        WaitlistEntry.objects.create(
            student=fatima,
            cycle=cycle_main,
            tier=1,
            tier_label='Tier 1 · Medical / Hardship',
            position=2,
            priority_points=95,
            preferred_hostels='Cedar House · Any Single',
            room_type_preference='Single room',
            status='offered',
            offer_bed_label='Cedar · C-114A',
            offer_expires_at=now + timedelta(hours=26),
            notes='Medical clinical accommodation priority band 1.'
        )
        WaitlistEntry.objects.create(
            student=jon,
            cycle=cycle_main,
            tier=2,
            tier_label='Tier 2 · Distance Priority',
            position=3,
            priority_points=84,
            preferred_hostels='Pine Lodge or Willow Hall',
            room_type_preference='Twin room',
            status='active',
            notes='Distance from campus: 142 km. Next in line for Pine Lodge vacancy.'
        )
        WaitlistEntry.objects.create(
            student=tariq,
            cycle=cycle_main,
            tier=2,
            tier_label='Tier 2 · Distance Priority',
            position=4,
            priority_points=81,
            preferred_hostels='Maple Court · Ensuite',
            room_type_preference='Ensuite room',
            status='active',
            notes='Distance from campus: 110 km.'
        )
        WaitlistEntry.objects.create(
            student=kwame,
            cycle=cycle_main,
            tier=2,
            tier_label='Tier 2 · Distance Priority',
            position=5,
            priority_points=78,
            preferred_hostels='Willow Hall or Pine Lodge',
            room_type_preference='Twin room',
            status='active',
            notes='International undergraduate awaiting visa doc clearance.'
        )
        WaitlistEntry.objects.create(
            student=elena,
            cycle=cycle_main,
            tier=3,
            tier_label='Tier 3 · General / Late Ballot',
            position=6,
            priority_points=65,
            preferred_hostels='Oak Residence or Maple Court',
            room_type_preference='Studio room',
            status='active',
            notes='Postgraduate late submission.'
        )

        # 10. Allocation Letters (M9)
        AllocationLetter.objects.create(
            letter_id='LTR-2025-001',
            student=amara,
            run=run_draft,
            hostel_name='Cedar House',
            room_number='C-214',
            bed_letter='A',
            room_type='Single room',
            fee_category='Standard University Residential',
            academic_year='2025/26',
            move_in_date='20 October 2025'
        )
        AllocationLetter.objects.create(
            letter_id='LTR-2025-002',
            student=leila,
            run=run_draft,
            hostel_name='Cedar House',
            room_number='C-119',
            bed_letter='A',
            room_type='Single room',
            fee_category='Standard University Residential',
            academic_year='2025/26',
            move_in_date='20 October 2025'
        )
        AllocationLetter.objects.create(
            letter_id='LTR-2025-003',
            student=sophie,
            run=run_draft,
            hostel_name='Willow Hall',
            room_number='W-201',
            bed_letter='A',
            room_type='Twin room',
            fee_category='Standard University Residential',
            academic_year='2025/26',
            move_in_date='20 October 2025'
        )

        # 11. Room Change Requests (M9)
        RoomChangeRequest.objects.create(
            student=amara,
            current_bed_label='Cedar · C-214A',
            preferred_hostel='Maple Court',
            reason_category='academic',
            details='Requesting transfer closer to Computer Science laboratory building for evening thesis work.',
            status='pending',
            created_at=now - timedelta(days=1)
        )
        RoomChangeRequest.objects.create(
            student=maya,
            current_bed_label='Maple · M-108B',
            preferred_hostel='Cedar House',
            reason_category='compatibility',
            details='Mutual roommate preference request with student STU-204810 (Amara Mensah).',
            status='approved',
            created_at=now - timedelta(days=5)
        )

        # 12. Immutable Audit Logs with Digital SHA-256 Seals (M9)
        audit_events = [
            ('Application Cycle CYC-2025-26 configured with statutory cohort quotas', 'System', now - timedelta(days=60)),
            ('Allocation run AR-2025-04 generated with reproducibility seed NST-7F3A29', 'Engine', now - timedelta(days=2)),
            ('Constraint solver executed: 1,942 allocated, 162 waitlisted, 8 exceptions', 'Engine', now - timedelta(days=2, hours=1)),
            ('Warden override logged for Daniel Kim (STU-204612): Ground-floor step-free transfer', 'Dr. Sarah Moore', now - timedelta(days=1, hours=4)),
            ('Waitlist Tier 1 offer generated for Willow W-102A (expires in 14h)', 'System', now - timedelta(hours=10)),
            ('Room change request #1 submitted by Amara Mensah (STU-204810)', 'Amara Mensah', now - timedelta(hours=8)),
            ('Prior cycle AR-2024-01 published with warden digital seal', 'Dr. Sarah Moore', now - timedelta(days=360)),
        ]

        for action, actor, ts in audit_events:
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S%z')
            digest = make_digest(action, actor, ts_str)
            AuditLog.objects.create(
                action=action,
                actor=actor,
                timestamp=ts,
                digest=digest
            )

        # 13. System Notifications
        Notification.objects.create(
            title='Your eligibility was verified for 2025/26',
            detail='Today, 10:42 AM',
            icon='bell',
            is_cream=False,
            created_at=now - timedelta(hours=2)
        )
        Notification.objects.create(
            title='New accessible rooms added at Willow Hall',
            detail='Yesterday',
            icon='building',
            is_cream=True,
            created_at=now - timedelta(days=1)
        )
        Notification.objects.create(
            title='Warden review completed for Draft AR-2025-04',
            detail='2 days ago',
            icon='check',
            is_cream=False,
            created_at=now - timedelta(days=2)
        )

        # 14. User Roles & Accounts
        # 14a. Admin / Warden Account
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'sarah.moore@nestora.edu', 'admin123')
        admin_user.first_name = 'Dr. Sarah'
        admin_user.last_name = 'Moore'
        admin_user.save()

        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={
                'role': 'admin',
                'title': 'Head Warden',
                'phone': '+44 20 7946 0912',
                'department': 'Residential Services & Student Housing',
                'office_location': 'Warden Central Office, North Quad, Suite 102'
            }
        )
        self.stdout.write("Created / Updated Warden Admin: admin / admin123")

        # 14b. Student Account
        student_user = User.objects.filter(username='student').first()
        if not student_user:
            student_user = User.objects.create_user('student', 'amara.m@university.edu', 'student123')
        student_user.first_name = 'Amara'
        student_user.last_name = 'Mensah'
        student_user.save()

        UserProfile.objects.update_or_create(
            user=student_user,
            defaults={
                'role': 'student',
                'student_profile': amara,
                'title': 'Computer Science & AI · Year 2',
                'phone': '+44 7700 900142',
                'department': 'School of Computer Science & Engineering',
                'office_location': 'Cedar House · Room C-214A'
            }
        )
        self.stdout.write("Created / Updated Student User: student / student123")

        self.stdout.write(self.style.SUCCESS("Successfully seeded comprehensive, well-structured Nestora PostgreSQL database!"))