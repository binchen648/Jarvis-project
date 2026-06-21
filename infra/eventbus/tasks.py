import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_pending_events(self):
    """推进事件状态: pending → processing → completed/failed

    每分钟执行一次，处理一批 pending 事件。
    当前为简化实现：仅推进状态，不执行具体回调。
    """
    from .models import Event

    batch = Event.objects.filter(status='pending')[:50]
    count = 0

    for event in batch:
        try:
            event.status = 'processing'
            event.save(update_fields=['status'])

            from .consumers import dispatch
            dispatch(event)

            event.status = 'completed'
            event.processed_at = timezone.now()
            event.save(update_fields=['status', 'processed_at'])
            count += 1

        except Exception as e:
            event.status = 'failed'
            event.error_message = str(e)[:500]
            event.save(update_fields=['status', 'error_message'])
            logger.error("Event %d failed: %s", event.id, e)

    if count:
        logger.info("Processed %d pending events", count)

    return {"processed": count}
