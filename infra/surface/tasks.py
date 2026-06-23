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


@shared_task(time_limit=300, soft_time_limit=240)
def run_all_producers():
    """Run all surface producers (goal, memory, wellness, agent) for all active users."""
    from django.contrib.auth import get_user_model
    from infra.surface.producers.runner import run_all
    
    User = get_user_model()
    active_users = User.objects.filter(is_active=True)
    total = 0
    
    for user in active_users:
        try:
            total += run_all(user)
        except Exception as e:
            logger.error('Surface producers failed for user %d: %s', user.pk, e)
    
    logger.info('Surface producers: created %d total events', total)
    return f'Created {total} events'
