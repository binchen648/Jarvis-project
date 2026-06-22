import logging
from ..registry import register, ActionResult

logger = logging.getLogger(__name__)

@register('discuss')
def handle_discuss(ctx):
    """Create a conversation with the source item as context."""
    from apps.chat.models import Conversation, Message
    # Build title from source
    title = _resolve_title(ctx)
    conv = Conversation.objects.create(user=ctx.user, title=title)
    content = _build_prompt(ctx)
    Message.objects.create(conversation=conv, role='user', content=content)
    logger.info("Created conversation %d from %s[%d]", conv.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, redirect=f"/chat/{conv.pk}/")

def _resolve_title(ctx):
    # Try to get a readable title from the source
    try:
        if ctx.source_type == 'goal':
            from apps.goals.models import Goal
            obj = Goal.objects.get(pk=ctx.source_id, user=ctx.user)
            return f"目标: {obj.title[:40]}"
        elif ctx.source_type == 'memory':
            from apps.memory.models import TrajectoryEvent
            obj = TrajectoryEvent.objects.get(pk=ctx.source_id, user=ctx.user)
            return f"记忆: {obj.title[:40]}"
        elif ctx.source_type == 'content':
            from apps.content.models import ProcessedContent
            obj = ProcessedContent.objects.get(pk=ctx.source_id)
            return f"内容: {obj.title[:40]}"
    except Exception:
        pass
    return f"{ctx.source_type}[{ctx.source_id}]"

def _build_prompt(ctx):
    try:
        if ctx.source_type == 'goal':
            from apps.goals.models import Goal
            obj = Goal.objects.get(pk=ctx.source_id, user=ctx.user)
            return f"关于目标「{obj.title}」:\n{obj.description or ''}\n\n请帮我分析这个目标并给出建议。"
        elif ctx.source_type == 'memory':
            from apps.memory.models import TrajectoryEvent
            obj = TrajectoryEvent.objects.get(pk=ctx.source_id, user=ctx.user)
            return f"关于记忆「{obj.title}」:\n{obj.description or ''}\n\n请帮我分析这条记忆。"
        elif ctx.source_type == 'content':
            from apps.content.models import ProcessedContent
            obj = ProcessedContent.objects.get(pk=ctx.source_id)
            return f"关于内容「{obj.title}」:\n{obj.description[:500]}\n\n请帮我分析。"
    except Exception:
        pass
    return f"请帮我分析这条{ctx.source_type}。"
