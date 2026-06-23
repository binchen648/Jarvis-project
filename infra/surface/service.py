"""Surface service — centralized event creation and status management.

All producers MUST use this service, never SurfaceEvent.objects.create() directly.
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def create_event(user, event_type, priority, title, description,
                 event_key='', source_type='', source_id=None,
                 cta=None):
    """Create a surface event with dedup via event_key.
    
    Returns (event, created) tuple.
    """
    from infra.llm.models import SurfaceEvent
    
    defaults = {
        'event_type': event_type,
        'priority': priority,
        'title': title,
        'description': description,
        'source_type': source_type,
        'source_id': source_id,
        'status': 'pending',
        'payload': {'cta': cta or {'action': 'discuss', 'label': '查看', 'icon': 'stars'}},
    }
    
    if event_key:
        event, created = SurfaceEvent.objects.get_or_create(
            user=user, event_key=event_key, defaults=defaults
        )
        if not created:
            # Update fields but preserve user-set status (read/acted/dismissed)
            for k, v in defaults.items():
                if k == 'status' and event.status != 'pending':
                    continue
                setattr(event, k, v)
            event.save(update_fields=[k for k in defaults.keys() if not (k == 'status' and event.status != 'pending')])
    else:
        event = SurfaceEvent.objects.create(user=user, **defaults)
        created = True
    
    return event, created


def mark_read(event):
    """Mark surface as read (user saw it)."""
    if event.status == 'pending':
        event.status = 'read'
        event.save(update_fields=['status'])
        return True
    return False


def mark_acted(event):
    """Mark surface as acted (user clicked CTA)."""
    event.status = 'acted'
    event.save(update_fields=['status'])
    return True


def mark_dismissed(event):
    """Mark surface as dismissed (user explicitly ignored)."""
    event.status = 'dismissed'
    event.save(update_fields=['status'])
    return True


def get_pending_surfaces(user):
    """Get all non-terminal surfaces for a user, sorted by priority."""
    from infra.llm.models import SurfaceEvent
    return SurfaceEvent.objects.filter(
        user=user, status__in=['pending', 'read']
    ).order_by('priority', '-created_at')[:20]


def get_stats(user):
    """Get surface stats for core-status."""
    from infra.llm.models import SurfaceEvent
    return {
        'pending_count': SurfaceEvent.objects.filter(user=user, status='pending').count(),
        'unread_count': SurfaceEvent.objects.filter(user=user, status='read').count(),
        'acted_today': SurfaceEvent.objects.filter(
            user=user, status='acted',
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count(),
        'last_event': SurfaceEvent.objects.filter(user=user).order_by('-created_at').first(),
    }
