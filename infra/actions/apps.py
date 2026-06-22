from django.apps import AppConfig


class ActionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infra.actions'
    verbose_name = 'Action Registry'

    def ready(self):
        from . import handlers  # noqa: F401 — triggers @register decorators
