"""Wellness producer — generates alerts for health/wellness patterns."""
import logging
from django.utils import timezone
from infra.surface.service import create_event

logger = logging.getLogger(__name__)

def produce(user):
    """Check wellness patterns and generate alerts."""
    from apps.wellness.models import WellnessRecord
    today = timezone.localdate()
    created = 0
    
    # Check if user recorded wellness today
    has_today = WellnessRecord.objects.filter(user=user, record_date=today).exists()
    if not has_today:
        event, is_new = create_event(
            user=user, event_type='reminder', priority=4,
            title='今日尚未记录身心健康',
            description='花 10 秒记录今天的心情和睡眠',
            event_key='wellness_today',
            cta={'action': 'discuss', 'label': '去记录', 'icon': 'heart'},
        )
        if is_new:
            created += 1
    
    # Check consecutive days without wellness record
    from django.db.models import Max
    last_record = WellnessRecord.objects.filter(user=user).aggregate(Max('record_date'))
    last_date = last_record.get('record_date__max')
    if last_date:
        days_since = (today - last_date).days
        if days_since >= 3:
            event, is_new = create_event(
                user=user, event_type='reminder', priority=3,
                title=f'已 {days_since} 天未记录健康数据',
                description='持续记录有助于 Jarvis 了解你的状态',
                event_key=f'wellness_streak:{today.isoformat()}',
                source_type='wellness',
                cta={'action': 'discuss', 'label': '立即记录', 'icon': 'heart'},
            )
            if is_new:
                created += 1
    
    logger.info('Wellness producer: created %d events for user %d', created, user.pk)
    return created
