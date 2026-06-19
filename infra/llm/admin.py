from django.contrib import admin
from .models import LLMCallLog, UserPersona


@admin.register(LLMCallLog)
class LLMCallLogAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'total_tokens', 'success', 'created_at']


@admin.register(UserPersona)
class UserPersonaAdmin(admin.ModelAdmin):
    list_display = ['user', 'version', 'last_built_at']
    search_fields = ['user__username']
