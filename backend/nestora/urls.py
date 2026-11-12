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

    # Student Portal App
    path('', include('student.urls')),
]
