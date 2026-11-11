from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from housing.models import Hostel, Student, Room, Bed, AllocationRun, AllocationRecord, UserProfile

class AdminAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hostel = Hostel.objects.create(
            name='Cedar House',
            slug='cedar-house',
            location='North Campus',
            price_per_semester=1850,
            beds_available=18,
            total_beds=60,
            image_url='https://example.com/cedar.jpg',
            tags=['Wi-Fi', 'Study rooms']
        )
        self.student_obj = Student.objects.create(
            name='Amara Mensah',
            student_id='STU-204810',
            email='amara.m@campus.edu',
            programme='Computer Science',
            year='Year 2'
        )
        self.student_user = User.objects.create_user(
            username='student',
            password='student123',
            email='amara.m@campus.edu'
        )
        UserProfile.objects.create(
            user=self.student_user,
            role='student',
            student_profile=self.student_obj,
            title='Computer Science · Year 2'
        )

        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@campus.edu',
            first_name='Dr. Sarah',
            last_name='Moore'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='admin',
            title='Head Warden'
        )

        self.run = AllocationRun.objects.create(
            run_id='AR-2025-04',
            title='Main allocation',
            status='draft'
        )
        self.record = AllocationRecord.objects.create(
            run=self.run,
            student=self.student_obj,
            assigned_bed_label='Cedar · C-214A',
            status='exception'
        )

    def test_student_cannot_access_admin_workspace(self):
        self.client.login(username='student', password='student123')
        
        admin_routes = ['admin-overview', 'bedmap', 'draft', 'runs']
        for r in admin_routes:
            res = self.client.get(reverse(r))
            self.assertEqual(res.status_code, 403, f"Student should be forbidden from {r}")

    def test_admin_can_access_admin_workspace(self):
        self.client.login(username='admin', password='admin123')
        
        admin_routes = ['admin-overview', 'bedmap', 'draft', 'runs']
        for r in admin_routes:
            res = self.client.get(reverse(r))
            self.assertEqual(res.status_code, 200, f"Admin should be allowed on {r}")

    def test_admin_override_api(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.post(
            reverse('api-draft-override'),
            data={'record_id': self.record.id, 'new_bed': 'Cedar House · C-216A', 'reason': 'Special accommodation'},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.record.refresh_from_db()
        self.assertEqual(self.record.assigned_bed_label, 'Cedar House · C-216A')
        self.assertEqual(self.record.status, 'clear')

    def test_admin_profile_update(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.get(reverse('admin-profile'))
        self.assertEqual(res.status_code, 200)

        post_res = self.client.post(reverse('admin-profile'), {
            'first_name': 'Sarah',
            'last_name': 'Moore-Smith',
            'email': 's.moore@nestora.edu',
            'title': 'Senior Warden Administrator',
            'phone': '+44 20 7946 0999',
            'department': 'Residential Operations',
            'office_location': 'North Quad 204'
        })
        self.assertEqual(post_res.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.last_name, 'Moore-Smith')
        self.assertEqual(self.admin_user.profile.title, 'Senior Warden Administrator')
