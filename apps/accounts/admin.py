from django.contrib import admin
from .models import User, UserPreference, FavoriteCreator, MonitorTopic, UserSettings


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active', 'date_joined']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_study_minutes']


@admin.register(FavoriteCreator)
class FavoriteCreatorAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'platform']


@admin.register(MonitorTopic)
class MonitorTopicAdmin(admin.ModelAdmin):
    list_display = ['user', 'keyword', 'push_frequency', 'is_active']


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'push_enabled']
