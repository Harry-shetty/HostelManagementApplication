"""
URL configuration for nestora project.
"""
from django.contrib import admin as django_admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # Favicon for browser tab
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),

    # Django Admin Site
    path('django-admin/', django_admin.site.urls),

    # Authentication (login / logout)
    path('', include('housing.urls')),

    # Admin Workspace App
    path('admin-workspace/', include('admin.urls')),

    # Convenience root redirects to Admin Workspace
    path('inventory/', RedirectView.as_view(url='/admin-workspace/inventory/', permanent=False)),
    path('bedmap/', RedirectView.as_view(url='/admin-workspace/inventory/', permanent=False)),
    path('draft/', RedirectView.as_view(url='/admin-workspace/draft/', permanent=False)),
    path('runs/', RedirectView.as_view(url='/admin-workspace/runs/', permanent=False)),
    path('reports/', RedirectView.as_view(url='/admin-workspace/reports/', permanent=False)),
    path('audit/', RedirectView.as_view(url='/admin-workspace/audit/', permanent=False)),

    # Student Portal App
    path('', include('student.urls')),
]
