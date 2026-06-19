from django.db import models


class UserProfile(models.Model):
    """用户主页/公开资料."""
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='profile'
    )
    bio = models.TextField(blank=True, max_length=500, verbose_name='个人简介')
    avatar = models.URLField(blank=True, max_length=500, verbose_name='头像 URL')
    social_links = models.JSONField(default=dict, blank=True, verbose_name='社交链接')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'userprofile_profile'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user}'s profile"
