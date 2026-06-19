from django.contrib import admin
from .models import TrajectoryEvent, SkillNode, UserLearningProgress, LearningPath, PathNode, \
    UserInterest, UserContentInteraction


@admin.register(TrajectoryEvent)
class TrajectoryEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'created_at']


@admin.register(SkillNode)
class SkillNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty', 'estimated_hours', 'learner_count']
    list_filter = ['category', 'difficulty']
    search_fields = ['name', 'category']


@admin.register(UserLearningProgress)
class UserLearningProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill', 'status', 'predicted_completion_days']
    list_filter = ['status']
    search_fields = ['user__username', 'skill__name']


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'user__username']


@admin.register(PathNode)
class PathNodeAdmin(admin.ModelAdmin):
    list_display = ['path', 'skill', 'order', 'status', 'estimated_minutes']
    list_filter = ['status']
    search_fields = ['path__title', 'skill__name']


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ['user', 'tag', 'weight', 'source', 'last_updated']
    list_filter = ['source']
    search_fields = ['user__username', 'tag']


@admin.register(UserContentInteraction)
class UserContentInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'action', 'created_at']
    list_filter = ['action']
