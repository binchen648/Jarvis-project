from django.contrib import admin
from .models import DashboardLayout


@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ['user']
