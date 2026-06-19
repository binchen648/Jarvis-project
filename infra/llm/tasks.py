"""Celery tasks for LLM service."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    time_limit=300,
    soft_time_limit=240,
    max_retries=2,
)
def build_all_personas():
    """Build/update personas for all active users. Runs daily."""
    from django.contrib.auth import get_user_model
    from infra.memory.persona_builder import build_persona

    User = get_user_model()
    active_users = User.objects.filter(is_active=True)
    count = 0
    for user in active_users:
        try:
            build_persona(user)
            count += 1
        except Exception as e:
            logger.error("Failed to build persona for user %d: %s", user.pk, e)
    return f'Built personas for {count} users'


@shared_task(
    time_limit=60,
    soft_time_limit=45,
    max_retries=1,
)
def build_user_persona(user_id):
    """Build/update persona for a single user. Triggered on-demand."""
    from django.contrib.auth import get_user_model
    from infra.memory.persona_builder import build_persona

    user = get_user_model().objects.get(pk=user_id)
    build_persona(user)
    return f'Built persona for user {user_id}'
