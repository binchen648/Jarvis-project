"""Celery tasks for surface events."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(time_limit=120, soft_time_limit=90)
def build_evening_summaries():
    """Generate evening summaries for all active users."""
    from django.contrib.auth import get_user_model
    from infra.surface.producers.evening_summary import produce
    
    User = get_user_model()
    active_users = User.objects.filter(is_active=True)
    count = 0
    
    for user in active_users:
        try:
            count += produce(user)
        except Exception as e:
            logger.error('Evening summary failed for user %d: %s', user.pk, e)
    
    logger.info('Evening summaries created for %d users', count)
    return f'Created {count} summaries'
