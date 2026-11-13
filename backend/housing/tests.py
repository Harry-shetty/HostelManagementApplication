from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from housing.models import Hostel, Student, Application, AllocationRun, AllocationRecord, UserProfile

class AuthenticationAndRoleSeparationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Hostel
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

        # Create Student model
        self.student_obj = Student.objects.create(
            name='Amara Mensah',
            student_id='STU-204810',
            email='amara.m@campus.edu',
            programme='Computer Science',
            year='Year 2'
        )

        self.app = Application.objects.create(
            application_id='NST-25-10482',
            student=self.student_obj,
            status='under_review'
        )

        # Create Student User Account
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

        # Create Admin / Warden User Account
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

        # Create Allocation Run & Record
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

    def test_unauthenticated_access_redirects_to_login(self):
        # Protected student portal
        res = self.client.get(reverse('overview'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('login'), res.url)

        # Protected admin workspace
        res_admin = self.client.get(reverse('admin-overview'))
        self.assertEqual(res_admin.status_code, 302)
        self.assertIn(reverse('login'), res_admin.url)

    def test_login_flow(self):
        # GET login page
        res = self.client.get(reverse('login'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Sign in to Nestora')

        # Invalid credentials
        res_fail = self.client.post(reverse('login'), {'username': 'student', 'password': 'wrongpassword'})
        self.assertEqual(res_fail.status_code, 200)
        self.assertContains(res_fail, 'Invalid credentials')

        # Successful student login
        res_success = self.client.post(reverse('login'), {'username': 'student', 'password': 'student123'}, follow=True)
        self.assertEqual(res_success.status_code, 200)
        self.assertContains(res_success, 'Your next chapter')

    def test_student_role_permissions(self):
        self.client.login(username='student', password='student123')

        # Allowed student routes
        self.assertEqual(self.client.get(reverse('overview')).status_code, 200)
        self.assertEqual(self.client.get(reverse('hostels')).status_code, 200)
        self.assertEqual(self.client.get(reverse('roommate')).status_code, 200)
        self.assertEqual(self.client.get(reverse('application')).status_code, 200)
        self.assertEqual(self.client.get(reverse('status')).status_code, 200)

        # Restricted admin routes -> 403 Forbidden
        res_admin_ov = self.client.get(reverse('admin-overview'))
        self.assertEqual(res_admin_ov.status_code, 403)
        self.assertContains(res_admin_ov, 'Administrator Access Required', status_code=403)

        self.assertEqual(self.client.get(reverse('bedmap')).status_code, 403)
        self.assertEqual(self.client.get(reverse('draft')).status_code, 403)
        self.assertEqual(self.client.get(reverse('runs')).status_code, 403)

    def test_admin_role_permissions(self):
        self.client.login(username='admin', password='admin123')

        # Allowed admin routes
        self.assertEqual(self.client.get(reverse('admin-overview')).status_code, 200)
        self.assertEqual(self.client.get(reverse('bedmap')).status_code, 200)
        self.assertEqual(self.client.get(reverse('draft')).status_code, 200)
        self.assertEqual(self.client.get(reverse('runs')).status_code, 200)

        # Admin can also review student routes
        self.assertEqual(self.client.get(reverse('overview')).status_code, 200)

    def test_logout_flow(self):
        self.client.login(username='student', password='student123')
        res = self.client.get(reverse('logout'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('login'), res.url)

        # Verify logged out
        res_after = self.client.get(reverse('overview'))
        self.assertEqual(res_after.status_code, 302)

    def test_unique_bed_per_draft_constraint(self):
        from django.db import IntegrityError
        student2 = Student.objects.create(
            name='Test Student 2',
            student_id='STU-999999'
        )
        run = AllocationRun.objects.create(run_id='AR-TEST-01', title='Constraint Test')
        AllocationRecord.objects.create(
            run=run,
            student=self.student_obj,
            assigned_bed_label='Cedar · C-101A'
        )
        # UniqueConstraint prevents double-assignment at the database level
        with self.assertRaises(IntegrityError):
            AllocationRecord.objects.create(
                run=run,
                student=student2,
                assigned_bed_label='Cedar · C-101A'
            )

    def test_socketio_broadcasting(self):
        from housing.sockets import sio, broadcast_bed_update, broadcast_allocation_override, broadcast_notification
        self.assertIsNotNone(sio)
        # Verify broadcasting helpers execute without exceptions
        broadcast_bed_update(bed_label="Cedar House · C-101A", status="occupied", student_name="Test Student")
        broadcast_allocation_override(student_name="Test Student", new_bed="Cedar House · C-102B")
        broadcast_notification(title="Test", message="Real-time test message", level="info")

    def test_socketio_wsgi_endpoint(self):
        import io
        from nestora.wsgi import application
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/socket.io/',
            'QUERY_STRING': 'EIO=4&transport=polling',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8000',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': io.BytesIO(b''),
            'wsgi.errors': io.StringIO(),
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        status_headers = []
        def start_response(status, headers):
            status_headers.append((status, headers))
        response = application(environ, start_response)
        self.assertTrue(len(status_headers) > 0)
        self.assertTrue(status_headers[0][0].startswith('200'))
        content = b''.join(response)
        self.assertIn(b'"sid":', content)
