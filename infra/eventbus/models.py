from django.db import models


class Event(models.Model):
    """事件总线 - 事件记录."""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, null=True, blank=True,
        related_name='events', verbose_name='用户'
    )
    event_type = models.CharField(max_length=200, verbose_name='事件类型')
    payload = models.JSONField(default=dict, verbose_name='事件数据')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态'
    )
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'eventbus_event'
        verbose_name = '事件'
        verbose_name_plural = '事件'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"{self.event_type}({self.status})"
