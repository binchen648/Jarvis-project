"""Memory producer — generates reminders for stale/important memories."""
import logging
from django.utils import timezone
from infra.surface.service import create_event

logger = logging.getLogger(__name__)

def produce(user):
    """Generate reminders for memories not reviewed in 7+ days."""
    from apps.memory.models import TrajectoryEvent
    week_ago = timezone.now() - timezone.timedelta(days=7)
    created = 0
    
    # Recent memories (last 7 days) — suggest review if over 3 days without new ones
    recent = TrajectoryEvent.objects.filter(
        user=user, happened_at__gte=week_ago
    ).count()
    
    if recent == 0:
        event, is_new = create_event(
            user=user, event_type='reminder', priority=3,
            title='近 7 天无新记忆',
            description='Jarvis 建议花 5 分钟回顾一下学习进展',
            event_key='memory_stale:7d',
            cta={'action': 'discuss', 'label': '回顾一下', 'icon': 'bell'},
        )
        if is_new:
            created += 1
    
    logger.info('Memory producer: created %d events for user %d', created, user.pk)
    return created
