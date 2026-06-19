from django.db import models


class DashboardLayout(models.Model):
    """Dashboard 布局配置."""
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='dashboard_layout'
    )
    layout_config = models.JSONField(default=dict, verbose_name='布局配置')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_layout'
        verbose_name = 'Dashboard 布局'
        verbose_name_plural = 'Dashboard 布局'

    def __str__(self):
        return f"{self.user}'s dashboard"
