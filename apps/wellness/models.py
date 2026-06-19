from django.db import models


class HealthSuggestion(models.Model):
    """系统生成的健康建议."""
    SUGGESTION_TYPES = [
        ('break', '休息'),
        ('eye', '护眼'),
        ('posture', '坐姿'),
        ('exercise', '运动'),
        ('sleep', '睡眠'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='health_suggestions'
    )
    suggestion_type = models.CharField(
        max_length=20, choices=SUGGESTION_TYPES, verbose_name='建议类型'
    )
    content = models.TextField(verbose_name='建议内容')
    trigger_reason = models.CharField(max_length=100, verbose_name='触发原因')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wellness_suggestion'
        verbose_name = '健康建议'
        verbose_name_plural = '健康建议'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='wellness_suggestion_user_read'),
        ]

    def __str__(self):
        return f"{self.get_suggestion_type_display()} - {self.user}"


class WellnessRecord(models.Model):
    """身心健康记录."""
    MOOD_CHOICES = [
        (1, '很差'),
        (2, '较差'),
        (3, '一般'),
        (4, '良好'),
        (5, '很好'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='wellness_records'
    )
    mood_score = models.IntegerField(choices=MOOD_CHOICES, verbose_name='心情评分')
    sleep_hours = models.FloatField(null=True, blank=True, verbose_name='睡眠时长')
    exercise_minutes = models.IntegerField(null=True, blank=True, verbose_name='运动时长(分钟)')
    note = models.TextField(blank=True, verbose_name='备注')
    record_date = models.DateField(auto_now_add=True, verbose_name='记录日期')

    class Meta:
        db_table = 'wellness_record'
        verbose_name = '身心健康记录'
        verbose_name_plural = '身心健康记录'
        ordering = ['-record_date']
        indexes = [
            models.Index(fields=['user', 'record_date'], name='wellness_record_user_date'),
        ]

    def __str__(self):
        return f"{self.user} - {self.record_date} - {self.get_mood_score_display()}"
