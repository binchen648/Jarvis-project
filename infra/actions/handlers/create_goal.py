import logging
from ..registry import register, ActionResult
from ..resolvers import resolve_object, resolve_title, resolve_description

logger = logging.getLogger(__name__)


@register('create_goal')
def handle_create_goal(ctx):
    obj = resolve_object(ctx.source_type, ctx.source_id, user=ctx.user)
    title = resolve_title(ctx.source_type, obj)
    desc = resolve_description(ctx.source_type, obj)
    from apps.goals.models import Goal
    g = Goal.objects.create(
        user=ctx.user,
        title=f'学习: {title}'[:200],
        description=desc,
        status='active',
    )
    logger.info('Created goal %d from %s[%d]', g.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, redirect=f'/goals/{g.pk}/')
