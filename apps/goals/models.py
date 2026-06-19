from django.db import models


class Goal(models.Model):
    """学习目标."""
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('completed', '已完成'),
        ('abandoned', '已放弃'),
    ]

    GOAL_TYPE_CHOICES = [
        ('custom', '自定义'),
        ('reading', '阅读'),
        ('coding', '编码练习'),
        ('study', '学习'),
        ('project', '项目'),
    ]

    CATEGORY_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '季度'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='goals'
    )
    title = models.CharField(max_length=300, verbose_name='目标标题')
    description = models.TextField(blank=True, verbose_name='目标描述')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态'
    )
    deadline = models.DateField(null=True, blank=True, verbose_name='截止日期')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- 新增字段 ---
    goal_type = models.CharField(
        max_length=20, choices=GOAL_TYPE_CHOICES, default='custom', verbose_name='目标类型'
    )
    target_value = models.FloatField(null=True, blank=True, verbose_name='目标值')
    target_unit = models.CharField(max_length=20, blank=True, verbose_name='目标单位')
    category = models.CharField(
        max_length=10, choices=CATEGORY_CHOICES, default='daily', verbose_name='周期类别'
    )
    is_recurring = models.BooleanField(default=False, verbose_name='是否循环')

    class Meta:
        db_table = 'goals_goal'
        verbose_name = '学习目标'
        verbose_name_plural = '学习目标'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='goals_goal_user_status'),
        ]

    def __str__(self):
        return self.title


class GoalProgress(models.Model):
    """目标进度记录."""
    goal = models.ForeignKey(
        Goal, on_delete=models.CASCADE, related_name='progress_records'
    )
    progress_percent = models.FloatField(default=0.0, verbose_name='进度百分比')
    note = models.TextField(blank=True, verbose_name='备注')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'goals_progress'
        verbose_name = '目标进度'
        verbose_name_plural = '目标进度'
        ordering = ['-recorded_at']


class GoalSession(models.Model):
    """学习记录 — 用户的学习时段记录."""

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='goal_sessions'
    )
    goal = models.ForeignKey(
        Goal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联目标'
    )
    date = models.DateField(auto_now_add=True, verbose_name='记录日期')
    duration_minutes = models.IntegerField(verbose_name='学习时长(分钟)')
    note = models.TextField(blank=True, verbose_name='备注')
    content_ref = models.ForeignKey(
        'content.ProcessedContent', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='关联内容'
    )

    class Meta:
        db_table = 'goals_session'
        verbose_name = '学习记录'
        verbose_name_plural = '学习记录'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date'], name='goals_session_user_date'),
        ]

    def __str__(self):
        goal_label = self.goal.title if self.goal else '无关联目标'
        return f'{self.date} {goal_label} ({self.duration_minutes}分钟)'
