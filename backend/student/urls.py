from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path('hostels/', views.hostels_view, name='hostels'),
    path('hostels/dismiss-prompt/', views.api_dismiss_roommate_prompt, name='dismiss-roommate-prompt'),
    path('roommate/', views.roommate_view, name='roommate'),
    path('roommate/submit/', views.submit_roommate_quiz_view, name='submit-roommate-quiz'),
    path('application/', views.application_view, name='application'),
    path('application/submit/', views.submit_application_view, name='submit-application'),
    path('status/', views.status_view, name='status'),
    path('status/view/', views.status_view, name='student-status'),
    path('status/letter/', views.student_letter_view, name='student-letter'),
    path('status/room-change/', views.submit_room_change_view, name='student-room-change'),
    path('hostel-change/', views.hostel_change_view, name='hostel-change'),
    path('hostel-change/submit/', views.submit_hostel_change_request, name='submit-hostel-change'),
    path('applications/', views.applications_view, name='student-applications'),
    path('waiting/', views.waiting_list_view, name='student-waiting-list'),
    path('profile/', views.profile_view, name='student-profile'),
    path('section/<str:section>/', views.placeholder_view, name='placeholder'),

    # APIs
    path('api/hostels/', views.api_hostels, name='api-hostels'),
    path('api/matches/<int:match_id>/save/', views.api_toggle_save_match, name='api-toggle-match'),
]

