from django.db import models


class Conversation(models.Model):
    """AI 对话会话."""
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='conversations'
    )
    title = models.CharField(max_length=300, blank=True, verbose_name='对话标题')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversation'
        verbose_name = '对话'
        verbose_name_plural = '对话'
        ordering = ['-updated_at']


class Message(models.Model):
    """对话消息."""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI'),
        ('system', '系统'),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='角色')
    content = models.TextField(verbose_name='消息内容')
    tokens_used = models.IntegerField(null=True, blank=True, verbose_name='消耗 Token')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
        verbose_name = '消息'
        verbose_name_plural = '消息'
        ordering = ['created_at']
