import logging
from django.utils import timezone
from ..registry import register, ActionResult

logger = logging.getLogger(__name__)

@register('save_memory')
def handle_save_memory(ctx):
    """Save the source item as a TrajectoryEvent (memory)."""
    from apps.memory.models import TrajectoryEvent

    title, description = _resolve_content(ctx)
    event_type = ctx.payload.get('event_type', ctx.source_type)

    event = TrajectoryEvent.objects.create(
        user=ctx.user,
        event_type=_map_type(event_type),
        title=title,
        description=description,
        happened_at=timezone.now(),
    )
    logger.info("Created memory %d from %s[%d]", event.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, message="已保存到记忆", data={"memory_id": event.pk})

def _map_type(t):
    mapping = {'goal': 'achievement', 'content': 'learning', 'message': 'reflection', 'wellness': 'learning'}
    return mapping.get(t, 'learning')

def _resolve_content(ctx):
    try:
        if ctx.source_type == 'goal':
            from apps.goals.models import Goal
            obj = Goal.objects.get(pk=ctx.source_id, user=ctx.user)
            return f"🎯 目标: {obj.title[:60]}", obj.description or ''
        elif ctx.source_type == 'content':
            from apps.content.models import ProcessedContent
            obj = ProcessedContent.objects.get(pk=ctx.source_id)
            return f"📚 内容: {obj.title[:60]}", obj.description[:500] or ''
        elif ctx.source_type == 'message':
            from apps.chat.models import Message
            obj = Message.objects.get(pk=ctx.source_id)
            return f"💬 对话: {obj.content[:60]}", obj.content[:500]
    except Exception:
        pass
    return f"{ctx.source_type}[{ctx.source_id}]", ""
