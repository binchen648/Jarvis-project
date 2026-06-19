from django.contrib import admin
from .models import Creator, RawContent, ProcessedContent, ContentEmbedding, ContentVector


@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'is_active']


@admin.register(RawContent)
class RawContentAdmin(admin.ModelAdmin):
    list_display = ['source_url', 'crawled_at']


@admin.register(ProcessedContent)
class ProcessedContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'stage', 'content_type', 'quality_score']


@admin.register(ContentEmbedding)
class ContentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['content', 'model_name']


@admin.register(ContentVector)
class ContentVectorAdmin(admin.ModelAdmin):
    list_display = ['content', 'updated_at']
