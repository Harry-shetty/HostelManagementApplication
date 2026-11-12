from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_overview, name='admin-overview'),
    path('inventory/', views.bedmap_view, name='bedmap'),
    path('draft/', views.draft_review, name='draft'),
    path('runs/', views.runs_view, name='runs'),
    path('runs/create/', views.create_run_view, name='create-run'),
    path('runs/<str:run_id>/publish/', views.publish_run_view, name='publish-run'),
    path('reports/', views.reports_view, name='reports'),
    path('audit/', views.audit_view, name='audit'),
    path('applications/', views.applications_view, name='admin-applications'),
    path('waiting/', views.waiting_list_view, name='admin-waiting-list'),
    path('profile/', views.profile_view, name='admin-profile'),
    path('section/<str:section>/', views.placeholder_view, name='admin-placeholder'),

    # Admin APIs
    path('api/draft/override/', views.api_draft_override, name='api-draft-override'),
    path('api/bedmap/reassign/', views.api_reassign_bed, name='api-bedmap-reassign'),
]

