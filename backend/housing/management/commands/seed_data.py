from django.core.management.base import BaseCommand
from housing.models import (
    Hostel, Student, Room, Bed, Application, ApplicationPreference,
    RoommateProfile, RoommateSuggestion, AllocationRun, AllocationRecord,
    AuditLog, Notification
)

PHOTOS = {
    'cedar': 'https://images.unsplash.com/photo-1753764403695-f43eb7cbead4?auto=format&fit=crop&w=1200&q=85',
    'maple': 'https://images.unsplash.com/photo-1596276020587-8044fe049813?auto=format&fit=crop&w=1200&q=85',
    'willow': 'https://images.unsplash.com/photo-1709949908229-53f3898aceab?auto=format&fit=crop&w=1200&q=85',
    'oak': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=85',
    'pine': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=85',
}

class Command(BaseCommand):
    help = 'Seeds initial data for the Nestora student housing system'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Nestora housing data...")

        # Clear existing
        AllocationRecord.objects.all().delete()
        AllocationRun.objects.all().delete()
        ApplicationPreference.objects.all().delete()
        Application.objects.all().delete()
        RoommateSuggestion.objects.all().delete()
        RoommateProfile.objects.all().delete()
        Bed.objects.all().delete()
        Room.objects.all().delete()
        Hostel.objects.all().delete()
        Student.objects.all().delete()
        AuditLog.objects.all().delete()
        Notification.objects.all().delete()

        # 1. Hostels
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

        # 2. Students
        amara = Student.objects.create(
            name='Amara Mensah',
            student_id='STU-204810',
            email='amara.m@university.edu',
            programme='Computer Science',
            year='Year 2',
            avatar_initials='AM',
            avatar_color='green',
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
            eligibility_status='Verified'
        )
        leila = Student.objects.create(
            name='Leila Chen',
            student_id='STU-204588',
            email='leila.c@university.edu',
            programme='Economics',
            year='Year 3',
            avatar_initials='LC',
            avatar_color='blue',
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
            eligibility_status='Review'
        )
        jon = Student.objects.create(
            name='Jon Bell',
            student_id='STU-204490',
            email='jon.b@university.edu',
            programme='Business Analytics',
            year='Year 2',
            avatar_initials='JB',
            avatar_color='peach',
            eligibility_status='Verified'
        )

        # 3. Rooms and Beds for Cedar House (Floor 1, 2, 3)
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
                status_a = 'accessible' if is_accessible else ('occupied' if idx % 3 != 0 else 'available')
                student_a = amara if (room_num == 'C-214') else None
                if room_num == 'C-214':
                    status_a = 'occupied'

                Bed.objects.create(
                    room=room,
                    bed_letter='A',
                    status=status_a,
                    assigned_student=student_a,
                    notes='Draft assignment' if student_a else ''
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

        # 4. Application for Amara Mensah
        app = Application.objects.create(
            application_id='NST-25-10482',
            student=amara,
            academic_year='2025/26',
            status='under_review',
            progress_percentage=60,
            current_step=3,
            room_type_preference='Single room',
            additional_notes='Quiet study environment requested.'
        )
        ApplicationPreference.objects.create(application=app, hostel=cedar, rank=1)
        ApplicationPreference.objects.create(application=app, hostel=maple, rank=2)
        ApplicationPreference.objects.create(application=app, hostel=willow, rank=3)

        # 5. Roommate Profile and Suggestions
        RoommateProfile.objects.create(
            student=amara,
            sleep_schedule='10 PM – 12 AM',
            cleanliness='Generally tidy',
            noise_level='Low background noise',
            interests='Computer Science · Web Design · Reading'
        )
        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=maya,
            compatibility_score=92,
            align_items=['Similar sleep schedule', 'Quiet study time'],
            difference='Different social pace',
            is_best_match=True,
            is_saved=False
        )
        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=leila,
            compatibility_score=87,
            align_items=['Both early risers', 'Shared cleaning style'],
            difference='Different guest preference',
            is_best_match=False,
            is_saved=False
        )
        RoommateSuggestion.objects.create(
            target_student=amara,
            suggested_student=zara,
            compatibility_score=84,
            align_items=['Quiet evenings', 'Similar study habits'],
            difference='Different music habits',
            is_best_match=False,
            is_saved=False
        )

        # 6. Allocation Run & Records
        run = AllocationRun.objects.create(
            run_id='AR-2025-04',
            title='Main allocation',
            status='draft',
            reproducibility_seed='NST-7F3A29',
            allocated_count=1942,
            top_preference_percent=78.4,
            waitlisted_count=162,
            exceptions_count=8,
            validation_status='Passed'
        )

        AllocationRecord.objects.create(
            run=run,
            student=amara,
            assigned_bed_label='Cedar · C-214A',
            preference_matched='1st choice',
            eligibility_status='Verified',
            status='clear'
        )
        AllocationRecord.objects.create(
            run=run,
            student=maya,
            assigned_bed_label='Maple · M-108B',
            preference_matched='2nd choice',
            eligibility_status='Verified',
            status='clear'
        )
        AllocationRecord.objects.create(
            run=run,
            student=daniel,
            assigned_bed_label='Willow · W-302A',
            preference_matched='3rd choice',
            eligibility_status='Review',
            status='exception'
        )
        AllocationRecord.objects.create(
            run=run,
            student=leila,
            assigned_bed_label='Cedar · C-119A',
            preference_matched='1st choice',
            eligibility_status='Verified',
            status='clear'
        )
        AllocationRecord.objects.create(
            run=run,
            student=jon,
            assigned_bed_label='Pine · P-204B',
            preference_matched='Outside top 3',
            eligibility_status='Verified',
            status='exception'
        )

        # 7. Audit Logs & Notifications
        AuditLog.objects.create(action='Draft AR-2025-04 completed', actor='System')
        AuditLog.objects.create(action='Application NST-25-10482 verified', actor='A. Patel')
        AuditLog.objects.create(action='Bed C-214B marked reserved', actor='J. Okoro')
        AuditLog.objects.create(action='Waitlist position updated', actor='System')

        Notification.objects.create(
            title='Your eligibility was verified',
            detail='Today, 10:42 AM',
            icon='bell',
            is_cream=False
        )
        Notification.objects.create(
            title='New rooms at Willow Hall',
            detail='Yesterday',
            icon='building',
            is_cream=True
        )

        # 8. User Roles & Accounts
        from django.contrib.auth.models import User
        from housing.models import UserProfile

        # 8a. Admin / Warden Account
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'sarah.moore@nestora.edu', 'admin123')
        admin_user.first_name = 'Dr. Sarah'
        admin_user.last_name = 'Moore'
        admin_user.save()

        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={'role': 'admin', 'title': 'Head Warden'}
        )
        self.stdout.write("Created Warden Admin: admin / admin123")

        # 8b. Student Account
        student_user = User.objects.filter(username='student').first()
        if not student_user:
            student_user = User.objects.create_user('student', 'amara.m@university.edu', 'student123')
        student_user.first_name = 'Amara'
        student_user.last_name = 'Mensah'
        student_user.save()

        UserProfile.objects.update_or_create(
            user=student_user,
            defaults={'role': 'student', 'student_profile': amara, 'title': 'Computer Science · Year 2'}
        )
        self.stdout.write("Created Student User: student / student123")

        self.stdout.write(self.style.SUCCESS("Successfully seeded Nestora housing database!"))
