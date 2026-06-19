from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for Jarvis platform."""

    class Meta:
        db_table = 'accounts_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class UserPreference(models.Model):
    """用户偏好设置."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='preferences'
    )
    learning_tags = models.JSONField(
        default=list, blank=True, verbose_name='学习领域标签'
    )
    daily_study_minutes = models.IntegerField(
        default=60, verbose_name='每日学习时长(分钟)'
    )
    active_time_start = models.TimeField(
        default='09:00', verbose_name='活跃时间段-开始'
    )
    active_time_end = models.TimeField(
        default='22:00', verbose_name='活跃时间段-结束'
    )

    class Meta:
        db_table = 'accounts_user_preference'
        verbose_name = '用户偏好'
        verbose_name_plural = '用户偏好'

    def __str__(self):
        return f"{self.user}'s preferences"


class FavoriteCreator(models.Model):
    """用户收藏的 UP 主/创作者."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite_creators'
    )
    name = models.CharField(max_length=200, verbose_name='创作者名称')
    platform = models.CharField(max_length=50, verbose_name='平台')
    homepage_url = models.URLField(max_length=500, verbose_name='主页 URL')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_favorite_creator'
        verbose_name = '收藏创作者'
        verbose_name_plural = '收藏创作者'
        unique_together = ['user', 'name', 'platform']

    def __str__(self):
        return f"{self.name} ({self.platform})"


class MonitorTopic(models.Model):
    """AI 监控主题."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='monitor_topics'
    )
    keyword = models.CharField(max_length=200, verbose_name='监控关键词')
    push_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', '实时'),
            ('daily', '每日'),
            ('weekly', '每周'),
        ],
        default='daily',
        verbose_name='推送频率',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_monitor_topic'
        verbose_name = '监控主题'
        verbose_name_plural = '监控主题'
        unique_together = ['user', 'keyword']

    def __str__(self):
        return f"{self.keyword}"


class UserSettings(models.Model):
    """用户设置."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='settings'
    )
    push_enabled = models.BooleanField(default=True, verbose_name='推送开关')
    privacy_profile_public = models.BooleanField(
        default=False, verbose_name='个人资料公开'
    )

    class Meta:
        db_table = 'accounts_user_settings'
        verbose_name = '用户设置'
        verbose_name_plural = '用户设置'

    def __str__(self):
        return f"{self.user}'s settings"
