from django.contrib import admin
from .models import WellnessRecord, HealthSuggestion


@admin.register(WellnessRecord)
class WellnessRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_score', 'record_date']


@admin.register(HealthSuggestion)
class HealthSuggestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'suggestion_type', 'is_read', 'created_at']
    list_filter = ['suggestion_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'content', 'trigger_reason']
    date_hierarchy = 'created_at'
