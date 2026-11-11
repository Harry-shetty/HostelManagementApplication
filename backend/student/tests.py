from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from housing.models import Hostel, Student, Application, UserProfile

class StudentAppTests(TestCase):
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

    def test_unauthenticated_redirect(self):
        res = self.client.get(reverse('overview'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('login'), res.url)

    def test_student_routes_authenticated(self):
        self.client.login(username='student', password='student123')
        
        routes = ['overview', 'hostels', 'roommate', 'application', 'status']
        for r in routes:
            res = self.client.get(reverse(r))
            self.assertEqual(res.status_code, 200, f"Route {r} failed")

    def test_api_hostels(self):
        res = self.client.get(reverse('api-hostels'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('hostels', data)
        self.assertTrue(len(data['hostels']) > 0)

    def test_student_profile_update(self):
        self.client.login(username='student', password='student123')
        res = self.client.get(reverse('student-profile'))
        self.assertEqual(res.status_code, 200)

        post_res = self.client.post(reverse('student-profile'), {
            'name': 'Amara K. Mensah',
            'email': 'amara.new@campus.edu',
            'phone': '+44 7700 900555',
            'programme': 'Data Science',
            'year': 'Year 3',
            'emergency_contact': 'Kofi Mensah · +44 7700 900981',
            'bio': 'Updated bio description.'
        })
        self.assertEqual(post_res.status_code, 200)
        self.student_obj.refresh_from_db()
        self.assertEqual(self.student_obj.name, 'Amara K. Mensah')
        self.assertEqual(self.student_obj.programme, 'Data Science')
