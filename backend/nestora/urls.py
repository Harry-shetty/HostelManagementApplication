"""
URL configuration for nestora project.
"""
from django.contrib import admin as django_admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from housing import views as auth_views

urlpatterns = [
    # Favicon for browser tab
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),

    # Django Admin Site
    path('django-admin/', django_admin.site.urls),

    # Authentication
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),

    # Admin Workspace App
    path('admin-workspace/', include('admin.urls')),

    # Student Portal App
    path('', include('student.urls')),
]
