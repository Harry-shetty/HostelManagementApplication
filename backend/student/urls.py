from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path('hostels/', views.hostels_view, name='hostels'),
    path('roommate/', views.roommate_view, name='roommate'),
    path('application/', views.application_view, name='application'),
    path('status/', views.status_view, name='status'),
    path('profile/', views.profile_view, name='student-profile'),
    path('section/<str:section>/', views.placeholder_view, name='placeholder'),

    # APIs
    path('api/hostels/', views.api_hostels, name='api-hostels'),
    path('api/matches/<int:match_id>/save/', views.api_toggle_save_match, name='api-toggle-match'),
]

