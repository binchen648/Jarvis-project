from django.contrib import admin
from .models import Goal, GoalProgress, GoalSession


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'goal_type', 'deadline', 'is_recurring']
    list_filter = ['status', 'goal_type', 'category']
    search_fields = ['title', 'description']


@admin.register(GoalProgress)
class GoalProgressAdmin(admin.ModelAdmin):
    list_display = ['goal', 'progress_percent', 'recorded_at']


@admin.register(GoalSession)
class GoalSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'goal', 'date', 'duration_minutes']
    list_filter = ['date']
    search_fields = ['note']
