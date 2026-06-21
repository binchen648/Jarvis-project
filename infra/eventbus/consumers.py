"""Event consumers — react to events and create cross-module side effects.

Each consumer function receives an Event instance and performs side effects
like creating TrajectoryEvents, updating agent context, or sending notifications.

Register new consumers in the HANDLERS dict below.
"""
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Consumer registry ────────────────────────────────────────────────────────
# Maps event_type → handler function
# Each handler receives (event) where event is an Event model instance.

HANDLERS = {}


def register(event_type):
    """Decorator to register a handler for an event type."""
    def decorator(func):
        HANDLERS[event_type] = func
        return func
    return decorator


@register('goal.status_changed')
def handle_goal_status_changed(event):
    """Goal completed → create achievement TrajectoryEvent."""
    payload = event.payload or {}
    status = payload.get('status')
    if status != 'completed':
        return
    title = payload.get('title', '')
    if not title:
        return
    from apps.memory.models import TrajectoryEvent
    TrajectoryEvent.objects.create(
        user=event.user,
        event_type='achievement',
        title=f"🎯 达成目标: {title[:60]}",
        description=f"目标「{title}」已完成。",
        happened_at=timezone.now(),
    )
    logger.info("Created achievement event for goal '%s'", title[:40])


@register('goal.created')
def handle_goal_created(event):
    """New goal → create milestone TrajectoryEvent."""
    payload = event.payload or {}
    title = payload.get('title', '')
    if not title:
        return
    from apps.memory.models import TrajectoryEvent
    TrajectoryEvent.objects.create(
        user=event.user,
        event_type='milestone',
        title=f"🎯 新目标: {title[:60]}",
        description=f"创建了新目标「{title}」。",
        happened_at=timezone.now(),
    )
    logger.info("Created milestone event for new goal '%s'", title[:40])


@register('goal_session.created')
def handle_goal_session_created(event):
    """Learning session logged → create learning TrajectoryEvent."""
    payload = event.payload or {}
    minutes = payload.get('duration_minutes', 0)
    from apps.memory.models import TrajectoryEvent
    from apps.goals.models import Goal
    goal_title = ''
    goal_id = payload.get('goal_id')
    if goal_id:
        try:
            goal = Goal.objects.get(pk=goal_id)
            goal_title = goal.title[:40]
        except Goal.DoesNotExist:
            pass
    title = f"🧠 学习: {goal_title}" if goal_title else "🧠 学习记录"
    TrajectoryEvent.objects.create(
        user=event.user,
        event_type='learning',
        title=title[:80],
        description=f"学习了 {minutes} 分钟。" if minutes else "完成了一次学习记录。",
        happened_at=timezone.now(),
    )
    logger.info("Created learning event from goal session")


@register('chat.message_sent')
def handle_chat_message_sent(event):
    """User message sent → create reflection TrajectoryEvent."""
    payload = event.payload or {}
    preview = (payload.get('content_preview') or '')[:100]
    if not preview:
        return
    from apps.memory.models import TrajectoryEvent
    TrajectoryEvent.objects.create(
        user=event.user,
        event_type='reflection',
        title=f"💬 对话: {preview[:60]}",
        description=preview,
        happened_at=timezone.now(),
    )
    logger.info("Created reflection event from chat message")


@register('wellness.recorded')
def handle_wellness_recorded(event):
    """Wellness recorded → create health TrajectoryEvent."""
    payload = event.payload or {}
    mood = payload.get('mood_score', '—')
    sleep = payload.get('sleep_hours', '—')
    from apps.memory.models import TrajectoryEvent
    TrajectoryEvent.objects.create(
        user=event.user,
        event_type='learning',
        title=f"❤️ 健康记录",
        description=f"心情评分: {mood}，睡眠: {sleep} 小时",
        happened_at=timezone.now(),
    )
    logger.info("Created health event from wellness record")


def dispatch(event):
    """Dispatch an event to its registered handler."""
    handler = HANDLERS.get(event.event_type)
    if handler is None:
        return  # no handler registered — not an error
    try:
        handler(event)
    except Exception:
        logger.exception("Event handler failed for %s (event %d)", event.event_type, event.pk)
