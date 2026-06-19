"""Minimal URL configuration for wellness app tests."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('wellness/', include('apps.wellness.urls')),
]
