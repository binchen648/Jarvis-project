from django.apps import AppConfig


class EventbusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infra.eventbus'
    verbose_name = '事件总线'

    def ready(self):
        from . import signals  # noqa
