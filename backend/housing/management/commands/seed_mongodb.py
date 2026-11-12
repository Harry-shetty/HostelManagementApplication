"""
Django Management Command to Seed MongoDB Atlas with Nestora Collections and Mock Data.

Usage:
    python3 manage.py seed_mongodb
    python3 manage.py seed_mongodb --uri="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
    python3 manage.py seed_mongodb --db="nestora"
"""

import sys
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from housing.mongodb import get_mongo_uri, get_mongo_db_name

PHOTOS = {
    'cedar': 'https://images.unsplash.com/photo-1753764403695-f43eb7cbead4?auto=format&fit=crop&w=1200&q=85',
    'maple': 'https://images.unsplash.com/photo-1596276020587-8044fe049813?auto=format&fit=crop&w=1200&q=85',
    'willow': 'https://images.unsplash.com/photo-1709949908229-53f3898aceab?auto=format&fit=crop&w=1200&q=85',
    'oak': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=85',
    'pine': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=85',
}


class Command(BaseCommand):
    help = 'Seeds MongoDB Atlas with required Nestora collections and mock data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--uri',
            type=str,
            default='',
            help='MongoDB connection URI (overrides settings / environment variable)'
        )
        parser.add_argument(
            '--db',
            type=str,
            default='',
            help='Target database name (default: nestora)'
        )

    def handle(self, *args, **options):
        uri = options.get('uri') or get_mongo_uri()
        db_name = options.get('db') or get_mongo_db_name() or 'nestora'

        if not uri:
            self.stderr.write(self.style.ERROR(
                "\n[ERROR] No MongoDB URI provided.\n"
                "Please configure MONGODB_URI in your .env file, or pass it via:\n"
                "  python3 manage.py seed_mongodb --uri=\"mongodb+srv://<user>:<password>@cluster.mongodb.net/\"\n"
            ))
            sys.exit(1)

        self.stdout.write(self.style.NOTICE(f"\nConnecting to MongoDB Atlas... (Database: '{db_name}')"))

        try:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=8000, appname="NestoraSeeder")
            # Ping database
            client.admin.command('ping')
            self.stdout.write(self.style.SUCCESS("✓ Connected to MongoDB Atlas successfully!"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"\n[ERROR] Failed to connect to MongoDB Atlas: {exc}\n"))
            sys.exit(1)

        db = client[db_name]

        # -------------------------------------------------------------
        # Drop existing collections in target DB for clean re-seed
        # -------------------------------------------------------------
        self.stdout.write("Resetting existing collections...")
        collections_to_seed = [
            'hostels', 'rooms', 'beds', 'students', 'roommate_profiles',
            'applications', 'allocation_runs', 'allocation_records', 'audit_logs'
        ]
        for col_name in collections_to_seed:
            db[col_name].drop()

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # 1. Hostels Collection
        # -------------------------------------------------------------
        self.stdout.write("1. Creating 'hostels' collection...")
        hostels_data = [
            {
                'name': 'Cedar House',
                'slug': 'cedar-house',
                'location': 'North Campus · 4 min walk',
                'price_per_semester': 18500,
                'currency': 'INR',
                'beds_available': 18,
                'total_beds': 60,
                'occupancy_percent': 88,
                'image_url': PHOTOS['cedar'],
                'room_summary': 'Single & twin rooms',
                'tags': ['Wi-Fi', 'Study rooms', 'Laundry'],
                'created_at': now
            },
            {
                'name': 'Maple Court',
                'slug': 'maple-court',
                'location': 'Central Campus · 2 min walk',
                'price_per_semester': 20500,
                'currency': 'INR',
                'beds_available': 11,
                'total_beds': 55,
                'occupancy_percent': 79,
                'image_url': PHOTOS['maple'],
                'room_summary': 'Ensuite rooms',
                'tags': ['Gym', 'Courtyard', 'Kitchen'],
                'created_at': now
            },
            {
                'name': 'Willow Hall',
                'slug': 'willow-hall',
                'location': 'East Campus · 5 min walk',
                'price_per_semester': 16500,
                'currency': 'INR',
                'beds_available': 26,
                'total_beds': 70,
                'occupancy_percent': 74,
                'image_url': PHOTOS['willow'],
                'room_summary': 'Twin & triple rooms',
                'tags': ['Accessible', 'Library', 'Café'],
                'created_at': now
            },
            {
                'name': 'Oak Residence',
                'slug': 'oak-residence',
                'location': 'West Campus · 8 min walk',
                'price_per_semester': 17500,
                'currency': 'INR',
                'beds_available': 15,
                'total_beds': 50,
                'occupancy_percent': 68,
                'image_url': PHOTOS['oak'],
                'room_summary': 'Studio & single rooms',
                'tags': ['Quiet zone', 'Bicycle storage', 'Balcony'],
                'created_at': now
            },
            {
                'name': 'Pine Lodge',
                'slug': 'pine-lodge',
                'location': 'South Campus · 10 min walk',
                'price_per_semester': 15500,
                'currency': 'INR',
                'beds_available': 20,
                'total_beds': 45,
                'occupancy_percent': 56,
                'image_url': PHOTOS['pine'],
                'room_summary': 'Shared apartments',
                'tags': ['Garden', 'Games room', 'Dining hall'],
                'created_at': now
            }
        ]
        db.hostels.insert_many(hostels_data)
        db.hostels.create_index('slug', unique=True)

        # -------------------------------------------------------------
        # 2. Rooms & Beds Collections
        # -------------------------------------------------------------
        self.stdout.write("2. Creating 'rooms' and 'beds' collections...")
        rooms_data = [
            {'hostel_slug': 'cedar-house', 'room_number': 'C-101', 'floor': 'Floor 1', 'wing': 'North Wing', 'room_type': 'single', 'total_beds': 1, 'is_accessible': True},
            {'hostel_slug': 'cedar-house', 'room_number': 'C-102', 'floor': 'Floor 1', 'wing': 'North Wing', 'room_type': 'twin', 'total_beds': 2, 'is_accessible': False},
            {'hostel_slug': 'cedar-house', 'room_number': 'C-214', 'floor': 'Floor 2', 'wing': 'North Wing', 'room_type': 'twin', 'total_beds': 2, 'is_accessible': False},
            {'hostel_slug': 'cedar-house', 'room_number': 'C-215', 'floor': 'Floor 2', 'wing': 'North Wing', 'room_type': 'single', 'total_beds': 1, 'is_accessible': False},
            {'hostel_slug': 'cedar-house', 'room_number': 'C-216', 'floor': 'Floor 2', 'wing': 'North Wing', 'room_type': 'twin', 'total_beds': 2, 'is_accessible': False},
            {'hostel_slug': 'cedar-house', 'room_number': 'C-301', 'floor': 'Floor 3', 'wing': 'North Wing', 'room_type': 'studio', 'total_beds': 1, 'is_accessible': True},
        ]
        db.rooms.insert_many(rooms_data)
        db.rooms.create_index([('hostel_slug', 1), ('room_number', 1)], unique=True)

        beds_data = [
            {'room_number': 'C-101', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-101A', 'status': 'occupied', 'student_id': 'STU-204812'},
            {'room_number': 'C-102', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-102A', 'status': 'available', 'student_id': None},
            {'room_number': 'C-102', 'hostel_slug': 'cedar-house', 'bed_letter': 'B', 'bed_label': 'Cedar House · C-102B', 'status': 'reserved', 'student_id': 'STU-204813'},
            {'room_number': 'C-214', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-214A', 'status': 'occupied', 'student_id': 'STU-204810'},
            {'room_number': 'C-214', 'hostel_slug': 'cedar-house', 'bed_letter': 'B', 'bed_label': 'Cedar House · C-214B', 'status': 'occupied', 'student_id': 'STU-204811'},
            {'room_number': 'C-215', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-215A', 'status': 'available', 'student_id': None},
            {'room_number': 'C-216', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-216A', 'status': 'available', 'student_id': None},
            {'room_number': 'C-216', 'hostel_slug': 'cedar-house', 'bed_letter': 'B', 'bed_label': 'Cedar House · C-216B', 'status': 'occupied', 'student_id': 'STU-204814'},
            {'room_number': 'C-301', 'hostel_slug': 'cedar-house', 'bed_letter': 'A', 'bed_label': 'Cedar House · C-301A', 'status': 'accessible', 'student_id': None},
        ]
        db.beds.insert_many(beds_data)
        db.beds.create_index('bed_label', unique=True)

        # -------------------------------------------------------------
        # 3. Students Collection
        # -------------------------------------------------------------
        self.stdout.write("3. Creating 'students' collection...")
        students_data = [
            {
                'student_id': 'STU-204810',
                'name': 'Amara Mensah',
                'email': 'amara.m@campus.edu',
                'programme': 'Computer Science',
                'year': 'Year 2',
                'gender': 'Female',
                'nationality': 'Ghanaian',
                'eligibility_status': 'Verified',
                'phone': '+44 7700 900244',
                'emergency_contact': 'Kofi Mensah · +44 7700 900981',
                'bio': 'Second-year CS student, loves quiet study hours, baking, and weekend coding projects.',
                'created_at': now
            },
            {
                'student_id': 'STU-204811',
                'name': 'Priya Sharma',
                'email': 'priya.s@campus.edu',
                'programme': 'Data Science',
                'year': 'Year 2',
                'gender': 'Female',
                'nationality': 'Indian',
                'eligibility_status': 'Verified',
                'phone': '+44 7700 900582',
                'emergency_contact': 'Rajesh Sharma · +44 7700 900412',
                'bio': 'Data science major, early bird, tea enthusiast, loves plants and neat spaces.',
                'created_at': now
            },
            {
                'student_id': 'STU-204812',
                'name': 'Marcus Vance',
                'email': 'marcus.v@campus.edu',
                'programme': 'Mechanical Engineering',
                'year': 'Year 1',
                'gender': 'Male',
                'nationality': 'British',
                'eligibility_status': 'Verified',
                'phone': '+44 7700 900331',
                'emergency_contact': 'Sarah Vance · +44 7700 900119',
                'bio': 'First year engineer, enjoys running, quiet evenings, and library study sessions.',
                'created_at': now
            },
            {
                'student_id': 'STU-204813',
                'name': 'Elena Rostova',
                'email': 'elena.r@campus.edu',
                'programme': 'Architecture',
                'year': 'Year 3',
                'gender': 'Female',
                'nationality': 'Czech',
                'eligibility_status': 'Verified',
                'phone': '+44 7700 900714',
                'emergency_contact': 'Jan Rostov · +44 7700 900882',
                'bio': 'Architecture senior, night owl during studio projects, clean and respectful.',
                'created_at': now
            },
            {
                'student_id': 'STU-204814',
                'name': 'Tariq Al-Mansoor',
                'email': 'tariq.a@campus.edu',
                'programme': 'Economics & Finance',
                'year': 'Year 2',
                'gender': 'Male',
                'nationality': 'Jordanian',
                'eligibility_status': 'Verified',
                'phone': '+44 7700 900995',
                'emergency_contact': 'Omar Al-Mansoor · +44 7700 900662',
                'bio': 'Economics major, gym regular, tidy room policy, enjoys football on weekends.',
                'created_at': now
            }
        ]
        db.students.insert_many(students_data)
        db.students.create_index('student_id', unique=True)
        db.students.create_index('email', unique=True)

        # -------------------------------------------------------------
        # 4. Roommate Profiles Collection
        # -------------------------------------------------------------
        self.stdout.write("4. Creating 'roommate_profiles' collection...")
        roommate_profiles = [
            {
                'student_id': 'STU-204810',
                'sleep_schedule': 'midnight',
                'wake_up_time': '8:00 AM',
                'study_noise': 'silent',
                'cleanliness_level': 'very_tidy',
                'guest_frequency': 'rarely',
                'dietary_preference': 'Vegetarian friendly',
                'sharing_policy': 'Ask first',
                'ideal_roommate_bio': 'Looking for someone who respects quiet hours during exams and keeps shared spaces clean.',
                'compatibility_matches': [
                    {'student_id': 'STU-204811', 'compatibility_score': 94, 'shared_habits': ['Quiet study', 'Early mornings', 'Neat spaces']},
                    {'student_id': 'STU-204813', 'compatibility_score': 82, 'shared_habits': ['Tidy living', 'Respectful of sleep']}
                ]
            },
            {
                'student_id': 'STU-204811',
                'sleep_schedule': 'early_bird',
                'wake_up_time': '6:30 AM',
                'study_noise': 'low_music',
                'cleanliness_level': 'very_tidy',
                'guest_frequency': 'rarely',
                'dietary_preference': 'Vegetarian',
                'sharing_policy': 'Share essentials',
                'ideal_roommate_bio': 'Calm and focused student who enjoys tea, books, and maintaining an organized room.'
            }
        ]
        db.roommate_profiles.insert_many(roommate_profiles)
        db.roommate_profiles.create_index('student_id', unique=True)

        # -------------------------------------------------------------
        # 5. Applications Collection
        # -------------------------------------------------------------
        self.stdout.write("5. Creating 'applications' collection...")
        applications_data = [
            {
                'application_id': 'NST-25-10482',
                'student_id': 'STU-204810',
                'cycle': '2025/2026',
                'status': 'under_review',
                'submitted_at': datetime(2025, 9, 28, 16, 32, tzinfo=timezone.utc),
                'preferences': [
                    {'rank': 1, 'hostel_slug': 'cedar-house', 'room_type': 'single'},
                    {'rank': 2, 'hostel_slug': 'maple-court', 'room_type': 'ensuite'},
                    {'rank': 3, 'hostel_slug': 'willow-hall', 'room_type': 'twin'}
                ],
                'requested_roommate_id': 'STU-204811',
                'special_requirements': 'Ground or second floor preferred'
            },
            {
                'application_id': 'NST-25-10483',
                'student_id': 'STU-204811',
                'cycle': '2025/2026',
                'status': 'under_review',
                'submitted_at': datetime(2025, 9, 28, 17, 10, tzinfo=timezone.utc),
                'preferences': [
                    {'rank': 1, 'hostel_slug': 'cedar-house', 'room_type': 'twin'},
                    {'rank': 2, 'hostel_slug': 'maple-court', 'room_type': 'ensuite'}
                ],
                'requested_roommate_id': 'STU-204810'
            }
        ]
        db.applications.insert_many(applications_data)
        db.applications.create_index('application_id', unique=True)
        db.applications.create_index('student_id')

        # -------------------------------------------------------------
        # 6. Allocation Runs & Records Collections
        # -------------------------------------------------------------
        self.stdout.write("6. Creating 'allocation_runs' and 'allocation_records'...")
        run_data = {
            'run_id': 'AR-2025-04',
            'title': 'Main allocation 2025/26 Cycle',
            'status': 'draft',
            'created_by': 'Allocation Engine v4',
            'reproducibility_seed': 'seed_8492031_nestora',
            'total_students': 1942,
            'allocated_count': 1934,
            'exceptions_count': 8,
            'satisfaction_score': 94.6,
            'created_at': datetime(2025, 10, 6, 9, 42, tzinfo=timezone.utc)
        }
        db.allocation_runs.insert_one(run_data)
        db.allocation_runs.create_index('run_id', unique=True)

        records_data = [
            {
                'run_id': 'AR-2025-04',
                'student_id': 'STU-204810',
                'assigned_bed_label': 'Cedar House · C-214A',
                'status': 'exception',
                'preference_rank': 1,
                'explanation': 'Roommate mutual match requested (Priya Sharma). Pair allocated to Cedar C-214 twin room.',
                'audit_flag': 'Requires warden sign-off'
            },
            {
                'run_id': 'AR-2025-04',
                'student_id': 'STU-204811',
                'assigned_bed_label': 'Cedar House · C-214B',
                'status': 'clear',
                'preference_rank': 1,
                'explanation': 'Standard preference match with mutual roommate nomination.'
            },
            {
                'run_id': 'AR-2025-04',
                'student_id': 'STU-204812',
                'assigned_bed_label': 'Cedar House · C-101A',
                'status': 'clear',
                'preference_rank': 1,
                'explanation': 'First-year priority allocation. Single accessible room.'
            }
        ]
        db.allocation_records.insert_many(records_data)
        db.allocation_records.create_index([('run_id', 1), ('student_id', 1)], unique=True)

        # -------------------------------------------------------------
        # 7. Audit Logs Collection
        # -------------------------------------------------------------
        self.stdout.write("7. Creating 'audit_logs' collection...")
        audit_logs = [
            {
                'actor': 'System Administrator (Sarah Moore)',
                'action': 'Draft run generated with seed seed_8492031_nestora',
                'run_id': 'AR-2025-04',
                'timestamp': datetime(2025, 10, 6, 9, 45, tzinfo=timezone.utc),
                'ip_address': '192.168.1.104'
            },
            {
                'actor': 'Head Warden (Sarah Moore)',
                'action': 'Exception flagged for Amara Mensah (STU-204810): Roommate accommodation review',
                'run_id': 'AR-2025-04',
                'timestamp': datetime(2025, 10, 6, 10, 15, tzinfo=timezone.utc),
                'ip_address': '192.168.1.104'
            }
        ]
        db.audit_logs.insert_many(audit_logs)
        db.audit_logs.create_index('timestamp')

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            f"\n========================================================\n"
            f"✓ MongoDB Atlas Database '{db_name}' Seeded Successfully!\n"
            f"========================================================\n"
            f"  • hostels:             {db.hostels.count_documents({})} documents\n"
            f"  • rooms:               {db.rooms.count_documents({})} documents\n"
            f"  • beds:                {db.beds.count_documents({})} documents\n"
            f"  • students:            {db.students.count_documents({})} documents\n"
            f"  • roommate_profiles:   {db.roommate_profiles.count_documents({})} documents\n"
            f"  • applications:        {db.applications.count_documents({})} documents\n"
            f"  • allocation_runs:     {db.allocation_runs.count_documents({})} documents\n"
            f"  • allocation_records:  {db.allocation_records.count_documents({})} documents\n"
            f"  • audit_logs:          {db.audit_logs.count_documents({})} documents\n"
            f"========================================================\n"
        ))
