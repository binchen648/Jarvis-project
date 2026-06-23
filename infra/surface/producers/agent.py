"""Agent producer — generates insights from agent analysis."""
import logging
from infra.surface.service import create_event

logger = logging.getLogger(__name__)

def produce(user):
    """Check for stale conversations and suggest follow-up."""
    from apps.chat.models import Conversation
    from django.utils import timezone
    created = 0
    week_ago = timezone.now() - timezone.timedelta(days=7)
    
    # Conversations with no recent activity
    stale = Conversation.objects.filter(
        user=user, updated_at__lte=week_ago
    ).order_by('-updated_at')[:3]
    
    for conv in stale:
        event, is_new = create_event(
            user=user, event_type='suggestion', priority=3,
            title=f'继续上次对话: {conv.title or "未命名"}',
            description=f'已有 {(timezone.now() - conv.updated_at).days} 天未继续',
            event_key=f'stale_conv:{conv.pk}',
            source_type='message', source_id=conv.pk,
            cta={'action': 'discuss', 'label': '继续对话', 'icon': 'stars'},
        )
        if is_new:
            created += 1
    
    logger.info('Agent producer: created %d events for user %d', created, user.pk)
    return created
