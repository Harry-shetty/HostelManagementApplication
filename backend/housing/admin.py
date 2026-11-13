from django.contrib import admin
from .models import (
    Hostel, Student, Room, Bed, Application, ApplicationPreference,
    RoommateProfile, RoommateSuggestion, AllocationRun, AllocationRecord,
    AuditLog, Notification, UserProfile,
    AllocationCycle, EligibilityRule, WaitlistEntry, AllocationApproval,
    AllocationLetter, RoomChangeRequest
)

@admin.register(AllocationCycle)
class AllocationCycleAdmin(admin.ModelAdmin):
    list_display = ('cycle_id', 'title', 'academic_year', 'status', 'is_active', 'window_open', 'window_close')
    list_filter = ('status', 'academic_year', 'is_active')
    search_fields = ('cycle_id', 'title')

@admin.register(EligibilityRule)
class EligibilityRuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_mandatory', 'is_active')
    list_filter = ('category', 'is_mandatory', 'is_active')
    search_fields = ('code', 'name', 'description')

@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('position', 'student', 'tier_label', 'status', 'priority_points', 'offer_bed_label', 'offer_expires_at')
    list_filter = ('tier', 'status')
    search_fields = ('student__name', 'student__student_id', 'offer_bed_label')

@admin.register(AllocationApproval)
class AllocationApprovalAdmin(admin.ModelAdmin):
    list_display = ('run', 'approved_by', 'approver_role', 'is_published', 'approved_at', 'published_at')
    list_filter = ('is_published',)
    search_fields = ('run__run_id', 'approved_by')

@admin.register(AllocationLetter)
class AllocationLetterAdmin(admin.ModelAdmin):
    list_display = ('letter_id', 'student', 'hostel_name', 'room_number', 'bed_letter', 'generated_at')
    search_fields = ('letter_id', 'student__name', 'student__student_id', 'hostel_name')

@admin.register(RoomChangeRequest)
class RoomChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'current_bed_label', 'preferred_hostel', 'reason_category', 'status', 'created_at')
    list_filter = ('status', 'reason_category')
    search_fields = ('student__name', 'current_bed_label', 'preferred_hostel')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'title', 'student_profile')
    list_filter = ('role',)
    search_fields = ('user__username', 'title')

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price_per_semester', 'beds_available', 'total_beds', 'occupancy_percent')
    search_fields = ('name', 'location')
    prepopulated_fields = {'slug': ('name',)}

class BedInline(admin.TabularInline):
    model = Bed
    extra = 1

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'hostel', 'floor', 'wing', 'room_type', 'gender')
    list_filter = ('hostel', 'floor', 'room_type')
    search_fields = ('room_number',)
    inlines = [BedInline]

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'room', 'bed_letter', 'status', 'assigned_student')
    list_filter = ('status', 'room__hostel', 'room__floor')
    search_fields = ('room__room_number', 'assigned_student__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'programme', 'year', 'eligibility_status')
    list_filter = ('programme', 'year', 'eligibility_status')
    search_fields = ('name', 'student_id', 'email')

class PreferenceInline(admin.TabularInline):
    model = ApplicationPreference
    extra = 1

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'student', 'academic_year', 'status', 'progress_percentage')
    list_filter = ('status', 'academic_year')
    search_fields = ('application_id', 'student__name', 'student__student_id')
    inlines = [PreferenceInline]

@admin.register(RoommateProfile)
class RoommateProfileAdmin(admin.ModelAdmin):
    list_display = ('student', 'sleep_schedule', 'cleanliness', 'noise_level')

@admin.register(RoommateSuggestion)
class RoommateSuggestionAdmin(admin.ModelAdmin):
    list_display = ('target_student', 'suggested_student', 'compatibility_score', 'is_best_match', 'is_saved')
    list_filter = ('is_best_match', 'is_saved')

@admin.register(AllocationRun)
class AllocationRunAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'title', 'status', 'allocated_count', 'top_preference_percent', 'exceptions_count')
    list_filter = ('status',)

@admin.register(AllocationRecord)
class AllocationRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'run', 'assigned_bed_label', 'preference_matched', 'eligibility_status', 'status', 'is_overridden')
    list_filter = ('status', 'run', 'preference_matched', 'is_overridden')
    search_fields = ('student__name', 'student__student_id', 'assigned_bed_label')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'timestamp')
    search_fields = ('action', 'actor')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'detail', 'created_at')
