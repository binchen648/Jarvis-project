from django.db import models


class Creator(models.Model):
    """内容创作者 (UP主)."""
    name = models.CharField(max_length=200, verbose_name='创作者名称')
    platform = models.CharField(max_length=50, verbose_name='平台')
    homepage_url = models.URLField(max_length=500, unique=True, verbose_name='主页 URL')
    avatar_url = models.URLField(max_length=500, blank=True, verbose_name='头像 URL')
    description = models.TextField(blank=True, verbose_name='简介')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content_creator'
        verbose_name = '创作者'
        verbose_name_plural = '创作者'

    def __str__(self):
        return self.name


class RawContent(models.Model):
    """原始内容仓库."""
    source_url = models.URLField(max_length=1000, unique=True, verbose_name='来源 URL')
    raw_data = models.JSONField(default=dict, verbose_name='原始数据')
    raw_html = models.TextField(blank=True, verbose_name='原始 HTML')
    crawled_at = models.DateTimeField(auto_now_add=True, verbose_name='抓取时间')

    class Meta:
        db_table = 'content_raw'
        verbose_name = '原始内容'
        verbose_name_plural = '原始内容'

    def __str__(self):
        return f"Raw:{self.source_url[:50]}"


class ProcessedContent(models.Model):
    """处理后标准内容."""
    STAGE_CHOICES = [
        ('pending', '待处理'),
        ('active', '活跃'),
        ('cooling', '冷却'),
        ('archived', '已归档'),
    ]
    CONTENT_TYPE_CHOICES = [
        ('video', '视频'),
        ('article', '文章'),
        ('podcast', '播客'),
    ]

    raw = models.OneToOneField(
        RawContent, on_delete=models.CASCADE, related_name='processed'
    )
    creator = models.ForeignKey(
        Creator, on_delete=models.CASCADE, related_name='contents'
    )
    title = models.CharField(max_length=500, verbose_name='标题')
    description = models.TextField(blank=True, verbose_name='描述')
    url = models.URLField(max_length=1000, blank=True, default='', verbose_name='内容 URL')
    tags = models.JSONField(blank=True, default=list, verbose_name='标签')
    ai_summary = models.TextField(blank=True, verbose_name='AI 摘要')
    quality_score = models.FloatField(default=0.0, verbose_name='质量评分')
    stage = models.CharField(
        max_length=20, choices=STAGE_CHOICES, default='pending', verbose_name='阶段'
    )
    content_type = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, verbose_name='内容类型'
    )
    duration_minutes = models.IntegerField(null=True, blank=True, verbose_name='时长(分钟)')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content_processed'
        verbose_name = '处理内容'
        verbose_name_plural = '处理内容'
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['-published_at']),
        ]

    def __str__(self):
        return self.title


class ContentEmbedding(models.Model):
    """内容向量嵌入 (PgVector 768维)."""
    content = models.OneToOneField(
        ProcessedContent, on_delete=models.CASCADE, related_name='embedding'
    )
    embedding = models.JSONField(verbose_name='嵌入向量')  # PgVector field will be added later
    model_name = models.CharField(max_length=100, default='bge-small-zh-v1.5')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_embedding'
        verbose_name = '内容向量'
        verbose_name_plural = '内容向量'


class ContentVector(models.Model):
    """向量存储 — 增量计算"""
    EMBEDDING_STATUS_CHOICES = [
        ('pending', '未生成'),
        ('processing', '生成中'),
        ('completed', '已完成'),
        ('failed', '生成失败'),
    ]
    content = models.OneToOneField(ProcessedContent, on_delete=models.CASCADE, primary_key=True, verbose_name="内容")
    embedding = models.JSONField(blank=True, null=True, verbose_name="嵌入向量")
    embedding_status = models.CharField(
        max_length=20, choices=EMBEDDING_STATUS_CHOICES, default='pending', verbose_name='嵌入状态'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'content_vector'
        verbose_name = '内容向量'
        verbose_name_plural = '内容向量'

    def __str__(self):
        return f"Vector for {self.content.title[:30]}"


class UserSubmittedContent(models.Model):
    """用户通过 URL 提交的内容（替代爬虫方案）."""
    url = models.URLField(max_length=1000, verbose_name='来源 URL')
    title = models.CharField(max_length=500, blank=True, verbose_name='标题')
    body_text = models.TextField(blank=True, verbose_name='正文')
    summary = models.TextField(blank=True, verbose_name='摘要')
    submitted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='提交者')
    is_active = models.BooleanField(default=True, verbose_name='是否展示')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='提交时间')

    class Meta:
        db_table = 'content_user_submitted'
        verbose_name = '用户提交内容'
        verbose_name_plural = '用户提交内容'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.url[:50]
