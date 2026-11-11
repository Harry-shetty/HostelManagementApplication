from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Warden / Housing Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_profile = models.OneToOneField('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profile')
    title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True, default='+44 20 7946 0912')
    department = models.CharField(max_length=120, blank=True, default='Residential Services & Student Housing')
    office_location = models.CharField(max_length=120, blank=True, default='Warden Central Office, North Quad, Suite 102')

    def is_student(self):
        return self.role == 'student'

    def is_admin(self):
        return self.role == 'admin' or self.user.is_staff or self.user.is_superuser

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Hostel(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    location = models.CharField(max_length=200)
    price_per_semester = models.IntegerField(default=1800)
    beds_available = models.IntegerField(default=10)
    total_beds = models.IntegerField(default=60)
    occupancy_percent = models.IntegerField(default=75)
    image_url = models.URLField(max_length=500)
    room_summary = models.CharField(max_length=150, default='Single & twin rooms')
    tags = models.JSONField(default=list)  # e.g. ['Wi-Fi', 'Study rooms', 'Laundry']

    def __str__(self):
        return self.name

    @property
    def formatted_price(self):
        return f"₹{self.price_per_semester:,}"

class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True)
    programme = models.CharField(max_length=100, default='Computer Science')
    year = models.CharField(max_length=30, default='Year 2')
    avatar_initials = models.CharField(max_length=5, blank=True)
    avatar_color = models.CharField(max_length=20, default='green')
    phone = models.CharField(max_length=30, blank=True, default='+44 7700 900142')
    emergency_contact = models.CharField(max_length=150, blank=True, default='Kofi Mensah · +44 7700 900981 (Parent)')
    bio = models.TextField(blank=True, default='Second-year CS student interested in software engineering. Quiet during weeknights, prefer clean and friendly shared living.')
    eligibility_status = models.CharField(
        max_length=20,
        choices=[('Verified', 'Verified'), ('Review', 'Review'), ('Pending', 'Pending')],
        default='Verified'
    )

    def save(self, *args, **kwargs):
        if not self.avatar_initials and self.name:
            parts = self.name.split()
            self.avatar_initials = ''.join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Room(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)  # e.g. C-201, C-214
    floor = models.CharField(max_length=20, default='Floor 2')
    wing = models.CharField(max_length=50, default='North wing')
    gender = models.CharField(max_length=20, default='Female')
    access_type = models.CharField(max_length=30, default='Standard')
    room_type = models.CharField(
        max_length=20,
        choices=[('Single', 'Single room'), ('Twin', 'Twin room'), ('Triple', 'Triple room')],
        default='Twin'
    )

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"{self.hostel.name} · {self.room_number}"

class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_letter = models.CharField(max_length=5)  # A, B, C
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('reserved', 'Reserved'),
            ('accessible', 'Accessible')
        ],
        default='available'
    )
    assigned_student = models.ForeignKey(
        Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_beds'
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['room', 'bed_letter']

    def __str__(self):
        return f"{self.room.room_number}{self.bed_letter} ({self.status})"

class Application(models.Model):
    application_id = models.CharField(max_length=30, unique=True, default='NST-25-10482')
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='application')
    academic_year = models.CharField(max_length=20, default='2025/26')
    status = models.CharField(
        max_length=30,
        choices=[
            ('in_progress', 'In progress'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under review'),
            ('allocated', 'Allocated'),
            ('waitlisted', 'Waitlisted')
        ],
        default='under_review'
    )
    progress_percentage = models.IntegerField(default=60)
    current_step = models.IntegerField(default=3)
    room_type_preference = models.CharField(max_length=30, default='Single room')
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.application_id} - {self.student.name}"

class ApplicationPreference(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='preferences')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['rank']
        unique_together = ('application', 'rank')

    def __str__(self):
        return f"#{self.rank} {self.hostel.name} for {self.application.application_id}"

class RoommateProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='roommate_profile')
    sleep_schedule = models.CharField(max_length=50, default='10 PM – 12 AM')
    cleanliness = models.CharField(max_length=50, default='Generally tidy')
    noise_level = models.CharField(max_length=50, default='Low background noise')
    interests = models.CharField(max_length=150, default='Photography · Cooking · Afrobeats')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Roommate Profile for {self.student.name}"

class RoommateSuggestion(models.Model):
    target_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='roommate_suggestions')
    suggested_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='suggested_as_roommate')
    compatibility_score = models.IntegerField(default=85)
    align_items = models.JSONField(default=list)
    difference = models.CharField(max_length=100, default='Different social pace')
    is_best_match = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-compatibility_score']

    def __str__(self):
        return f"{self.target_student.name} + {self.suggested_student.name} ({self.compatibility_score}%)"

class AllocationRun(models.Model):
    run_id = models.CharField(max_length=30, unique=True, default='AR-2025-04')
    title = models.CharField(max_length=100, default='Main allocation')
    status = models.CharField(
        max_length=30,
        choices=[
            ('draft', 'Draft v4'),
            ('review', 'Draft review'),
            ('approved', 'Warden approved'),
            ('published', 'Published')
        ],
        default='draft'
    )
    reproducibility_seed = models.CharField(max_length=40, default='NST-7F3A29')
    allocated_count = models.IntegerField(default=1942)
    top_preference_percent = models.DecimalField(max_digits=5, decimal_places=1, default=78.4)
    waitlisted_count = models.IntegerField(default=162)
    exceptions_count = models.IntegerField(default=8)
    validation_status = models.CharField(max_length=30, default='Passed')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.run_id} ({self.status})"

class AllocationRecord(models.Model):
    run = models.ForeignKey(AllocationRun, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assigned_bed_label = models.CharField(max_length=60, default='Cedar · C-214A')
    preference_matched = models.CharField(max_length=30, default='1st choice')
    eligibility_status = models.CharField(max_length=20, default='Verified')
    status = models.CharField(
        max_length=20,
        choices=[('clear', 'Clear'), ('exception', 'Exception')],
        default='clear'
    )
    override_reason = models.TextField(blank=True, null=True)
    is_overridden = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.student.name} -> {self.assigned_bed_label} [{self.status}]"

class AuditLog(models.Model):
    action = models.CharField(max_length=250)
    actor = models.CharField(max_length=100, default='System')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.actor}"

class Notification(models.Model):
    title = models.CharField(max_length=150)
    detail = models.CharField(max_length=100, default='Today, 10:42 AM')
    icon = models.CharField(max_length=30, default='bell')
    is_cream = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
