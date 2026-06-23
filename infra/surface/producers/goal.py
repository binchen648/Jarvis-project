"""Goal producer — generates surface events for goal-related alerts."""
import logging
from django.utils import timezone
from infra.surface.service import create_event

logger = logging.getLogger(__name__)

def produce(user):
    """Generate surface events for expiring goals and goal milestones."""
    from apps.goals.models import Goal
    today = timezone.localdate()
    created = 0
    
    # Expiring goals (deadline <= 3 days)
    expiring = Goal.objects.filter(
        user=user, status='active',
        deadline__gte=today, deadline__lte=today + timezone.timedelta(days=3)
    ).order_by('deadline')
    
    for g in expiring:
        days_left = (g.deadline - today).days
        event, is_new = create_event(
            user=user, event_type='alert', priority=1,
            title=f'目标即将截止: {g.title}',
            description=f'还剩 {days_left} 天' if days_left > 0 else '今天截止!',
            event_key=f'goal_deadline:{g.pk}',
            source_type='goal', source_id=g.pk,
            cta={'action': 'discuss', 'label': '制定计划', 'icon': 'clipboard'},
        )
        if is_new:
            created += 1
    
    logger.info('Goal producer: created %d events for user %d', created, user.pk)
    return created
