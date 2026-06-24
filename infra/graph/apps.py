from django.apps import AppConfig


class GraphInfraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infra.graph'
    verbose_name = '知识图谱'

    def ready(self):
        from django.db.models.signals import post_save
        from django.dispatch import receiver
        from .sync import sync_goal_to_graph

        @receiver(post_save, sender='goals.Goal')
        def auto_sync_goal(sender, instance, **kwargs):
            sync_goal_to_graph(instance)
