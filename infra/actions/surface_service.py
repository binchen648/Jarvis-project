"""Surface service — aggregates pending surface events from all sources.

This is the ONLY module that queries SurfaceEvent/Goal/Memory directly.
API views and handlers should NEVER import these models directly.
"""
import logging
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


def get_pending_events(user):
    """Return sorted list of pending surface events for a user.
    
    Returns:
        list of dicts, each with: id, type, priority, title, description,
        source: {type, id}, cta: {action, label, icon}
    """
    events = []
    
    # 1. SurfaceEvent records (from eventbus)
    try:
        from infra.llm.models import SurfaceEvent
        qs = SurfaceEvent.objects.filter(user=user, status='pending').order_by('priority', '-created_at')
        for se in qs:
            events.append({
                'id': se.pk,
                'type': se.event_type,
                'priority': se.priority,
                'title': se.title,
                'description': se.body,
                'source': {'type': se.event_type, 'id': se.pk},
                'cta': se.payload.get('cta', {'action': 'discuss', 'label': 'Discuss', 'icon': 'stars'}),
            })
    except Exception:
        logger.warning('SurfaceEvent query failed for user %d', user.pk)
    
    # 2. Expiring goals (deadline within 3 days)
    try:
        from apps.goals.models import Goal
        today = timezone.localdate()
        expiring = Goal.objects.filter(
            user=user, status='active',
            deadline__gte=today, deadline__lte=today + timezone.timedelta(days=3)
        ).order_by('deadline')[:3]
        for g in expiring:
            events.append({
                'id': f'goal_{g.pk}',
                'type': 'alert',
                'priority': 1,
                'title': f'目标即将截止: {g.title}',
                'description': f'还剩 {(g.deadline - today).days} 天',
                'source': {'type': 'goal', 'id': g.pk},
                'cta': {'action': 'discuss', 'label': '制定计划', 'icon': 'clipboard'},
            })
    except Exception:
        logger.warning('Expiring goals query failed for user %d', user.pk)
    
    # Sort by priority only (lower = more urgent). 
    # Sorting by secondary key would crash on mixed int/str ids.
    events.sort(key=lambda e: e['priority'])
    
    return events


def get_pending_count(user):
    """Return count of pending events (lightweight, for core status)."""
    count = 0
    try:
        from infra.llm.models import SurfaceEvent
        count += SurfaceEvent.objects.filter(user=user, status='pending').count()
    except Exception:
        pass
    try:
        from apps.goals.models import Goal
        today = timezone.localdate()
        count += Goal.objects.filter(
            user=user, status='active',
            deadline__gte=today, deadline__lte=today + timezone.timedelta(days=3)
        ).count()
    except Exception:
        pass
    return count
