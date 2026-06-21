from django.db import models


class LLMCallLog(models.Model):
    """LLM 调用日志."""
    model_name = models.CharField(max_length=100, verbose_name='模型名称')
    prompt_tokens = models.IntegerField(default=0, verbose_name='提示 Tokens')
    completion_tokens = models.IntegerField(default=0, verbose_name='生成 Tokens')
    total_tokens = models.IntegerField(default=0, verbose_name='总 Tokens')
    cost = models.FloatField(default=0.0, verbose_name='费用')
    duration_ms = models.IntegerField(default=0, verbose_name='耗时(毫秒)')
    success = models.BooleanField(default=True, verbose_name='是否成功')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'llm_call_log'
        verbose_name = 'LLM 调用日志'
        verbose_name_plural = 'LLM 调用日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_name} - {self.total_tokens}tokens"


class UserPersona(models.Model):
    """用户人格画像 — 由系统持续构建和压缩."""
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='persona',
        verbose_name='用户'
    )
    # LLM 生成的紧凑画像摘要 (~300 tokens)
    persona_summary = models.TextField(blank=True, verbose_name='画像摘要')
    # 结构化事实（用户主动告知或从对话提取）
    facts = models.JSONField(default=list, blank=True, verbose_name='用户事实')
    # 兴趣标签快照 [{"tag": "Python", "weight": 8.5}, ...]
    interests = models.JSONField(default=list, blank=True, verbose_name='兴趣标签')
    # 画像元数据
    version = models.IntegerField(default=0, verbose_name='画像版本')
    last_built_at = models.DateTimeField(null=True, blank=True, verbose_name='最后构建时间')
    last_signal_at = models.DateTimeField(
        null=True, blank=True, verbose_name='最后信号时间'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'llm_user_persona'
        verbose_name = '用户画像'
        verbose_name_plural = '用户画像'

    def __str__(self):
        return f"{self.user}'s persona (v{self.version})"


class MemoryEntry(models.Model):
    """多级记忆条目 — Hermes-inspired L1/L2/L3 记忆系统.

    L1 (Core Profile): 用户核心画像，每次会话自动加载
    L2 (Context): 近期上下文，按需加载到 system prompt
    L3 (Detail): 详细记录，仅通过 FTS5 搜索显式检索

    FTS5 搜索使用 django.contrib.postgres.search.SearchVector
    在查询时动态构建（不存储 SearchVectorField），减少模型耦合。
    Phase B 可升级为存储式 SearchVectorField + GIN 索引。
    """
    LEVEL_CHOICES = [
        (1, 'Core Profile'),
        (2, 'Context'),
        (3, 'Detail'),
    ]

    MEMORY_TYPES = [
        ('persona_summary', '画像摘要'),
        ('user_fact', '用户事实'),
        ('interest', '兴趣标签'),
        ('goal', '学习目标'),
        ('skill_progress', '技能进度'),
        ('conversation', '对话记录'),
        ('insight', '学习洞察'),
        ('wellness', '身心健康'),
        ('persona_history', '画像历史'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='memory_entries',
        verbose_name='用户'
    )
    level = models.IntegerField(choices=LEVEL_CHOICES, verbose_name='记忆级别')
    memory_type = models.CharField(
        max_length=30, choices=MEMORY_TYPES, verbose_name='记忆类型'
    )
    content = models.TextField(verbose_name='记忆内容')
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    weight = models.FloatField(default=1.0, verbose_name='权重(0-10)')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='过期时间')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    access_count = models.IntegerField(default=0, verbose_name='访问次数')
    accessed_at = models.DateTimeField(auto_now=True, verbose_name='最后访问')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'llm_memory_entry'
        verbose_name = '记忆条目'
        verbose_name_plural = '记忆条目'
        indexes = [
            models.Index(fields=['user', 'level'], name='mem_user_level'),
            models.Index(fields=['user', 'memory_type'], name='mem_user_type'),
            models.Index(fields=['user', 'is_active'], name='mem_user_active'),
            models.Index(fields=['expires_at'], name='mem_expires'),
        ]
        ordering = ['-weight', '-created_at']

    def __str__(self):
        return f"{self.user}-L{self.level}/{self.memory_type}"


class SurfaceEvent(models.Model):
    """AI Surface event — unified model for all surface cards (Alert, Suggestion, Reminder, Briefing, Summary)."""
    TYPE_CHOICES = [
        ('alert', 'Goal Alert'),
        ('suggestion', 'Smart Suggestion'),
        ('reminder', 'Memory Reminder'),
        ('briefing', 'Morning Briefing'),
        ('summary', 'Evening Summary'),
    ]
    PRIORITY_CHOICES = [
        (1, 'P1 - Alert'),
        (2, 'P2 - Suggestion'),
        (3, 'P3 - Reminder'),
        (4, 'P4 - Briefing'),
        (5, 'P5 - Summary'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shown', 'Shown'),
        ('dismissed', 'Dismissed'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='surface_events')
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=5)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'llm_surface_event'
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'event_type']),
        ]

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.title[:40]}"
