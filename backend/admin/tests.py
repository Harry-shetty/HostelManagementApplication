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

    def test_student_forbidden_from_create_run(self):
        self.client.login(username='student', password='student123')
        res = self.client.post(reverse('create-run'), {'title': 'Illegal Attempt'})
        self.assertEqual(res.status_code, 403)

    def test_admin_create_draft_run_creates_run_and_records(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.post(reverse('create-run'), {
            'title': 'Spring 2026 Special Cycle',
            'seed': 'NST-AA11BB',
            'strategy': 'optimal'
        })
        self.assertEqual(res.status_code, 302)
        self.assertIn('run_id=AR-2025-05', res.url)

        new_run = AllocationRun.objects.filter(run_id='AR-2025-05').first()
        self.assertIsNotNone(new_run)
        self.assertEqual(new_run.title, 'Spring 2026 Special Cycle')
        self.assertEqual(new_run.reproducibility_seed, 'NST-AA11BB')
        self.assertEqual(new_run.status, 'draft')
        self.assertTrue(new_run.records.exists())

        # Verify Audit Log
        from housing.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action__contains='AR-2025-05').exists())

    def test_admin_reassign_bed_api(self):
        self.client.login(username='admin', password='admin123')

        # Create rooms C-112 and C-216
        room_from = Room.objects.create(hostel=self.hostel, room_number='C-112', floor='Floor 1')
        bed_from = Bed.objects.create(room=room_from, bed_letter='A', status='occupied', assigned_student=self.student_obj)

        room_to = Room.objects.create(hostel=self.hostel, room_number='C-216', floor='Floor 2')
        bed_to = Bed.objects.create(room=room_to, bed_letter='A', status='available')

        res = self.client.post(
            reverse('api-bedmap-reassign'),
            data={
                'student_id': self.student_obj.student_id,
                'from_bed': 'Cedar · C-112A',
                'target_bed': 'Cedar · C-216A · Single',
                'run_id': 'AR-2025-04',
                'constraint_checked': True
            },
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['student_name'], self.student_obj.name)

        bed_from.refresh_from_db()
        bed_to.refresh_from_db()
        self.assertEqual(bed_from.status, 'available')
        self.assertIsNone(bed_from.assigned_student)
        self.assertEqual(bed_to.status, 'occupied')
        self.assertEqual(bed_to.assigned_student, self.student_obj)

        self.record.refresh_from_db()
        self.assertEqual(self.record.assigned_bed_label, 'Cedar · C-216A · Single')
        self.assertTrue(self.record.is_overridden)

        from housing.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action__contains='C-112A to Cedar · C-216A').exists())

    def test_applications_page_renders_mock_data(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.get('/section/applications/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Student applications &amp; quotas')
        self.assertContains(res, '2,104')
        self.assertContains(res, 'Amara Mensah')
        self.assertContains(res, 'NST-25-10482')

    def test_waiting_list_page_renders_mock_data(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.get('/section/waiting/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Priority waiting list &amp; offers')
        self.assertContains(res, '162')
        self.assertContains(res, 'Daniel Kim')
        self.assertContains(res, 'Tier 1 · Medical / Hardship')

    def test_publish_run_creates_approval_and_letters(self):
        from housing.models import AllocationApproval, AllocationLetter
        self.client.login(username='admin', password='admin123')
        res = self.client.post(
            reverse('publish-run', args=[self.run.run_id]),
            {'approver_role': 'Head Warden', 'approval_notes': 'Checked all quotas'}
        )
        self.assertEqual(res.status_code, 302)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, 'published')
        self.assertTrue(AllocationApproval.objects.filter(run=self.run, is_published=True).exists())
        self.assertTrue(AllocationLetter.objects.filter(student=self.student_obj).exists())

    def test_reports_view_renders_analytics(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.get(reverse('reports'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Reporting &amp; analytics')
        self.assertContains(res, 'CAMPUS OCCUPANCY')
        self.assertContains(res, 'Cedar House')

    def test_audit_view_renders_trail(self):
        self.client.login(username='admin', password='admin123')
        res = self.client.get(reverse('audit'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Audit log')
        self.assertContains(res, 'Tamper-Evident Governance Trail Active')
