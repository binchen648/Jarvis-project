import logging
from ..registry import register, ActionResult

logger = logging.getLogger(__name__)

@register('create_goal')
def handle_create_goal(ctx):
    """Create a Goal from the source item."""
    from apps.goals.models import Goal

    title = f"学习: {_resolve_title(ctx)}"[:200]
    description = _resolve_description(ctx)

    goal = Goal.objects.create(
        user=ctx.user,
        title=title,
        description=description,
        status='active',
    )
    logger.info("Created goal %d from %s[%d]", goal.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, redirect=f"/goals/{goal.pk}/")

def _resolve_title(ctx):
    try:
        if ctx.source_type == 'memory':
            from apps.memory.models import TrajectoryEvent
            obj = TrajectoryEvent.objects.get(pk=ctx.source_id, user=ctx.user)
            return obj.title[:60]
        elif ctx.source_type == 'content':
            from apps.content.models import ProcessedContent
            obj = ProcessedContent.objects.get(pk=ctx.source_id)
            return obj.title[:60]
        elif ctx.source_type == 'skill':
            return ctx.payload.get('skill_name', '')[:60]
    except Exception:
        pass
    return ctx.payload.get('title', f"{ctx.source_type}[{ctx.source_id}]")

def _resolve_description(ctx):
    try:
        if ctx.source_type == 'memory':
            from apps.memory.models import TrajectoryEvent
            obj = TrajectoryEvent.objects.get(pk=ctx.source_id, user=ctx.user)
            return obj.description or ''
        elif ctx.source_type == 'content':
            from apps.content.models import ProcessedContent
            obj = ProcessedContent.objects.get(pk=ctx.source_id)
            return f"来自: {obj.url or 'N/A'}\n\n{obj.description[:500]}"
    except Exception:
        pass
    return f"从{ctx.source_type}创建"
