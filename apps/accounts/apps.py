from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = '用户认证与偏好'

    def ready(self):
        import apps.accounts.signals  # noqa
