import logging
from ..registry import register, ActionResult
from ..resolvers import resolve_object, resolve_title, resolve_description

logger = logging.getLogger(__name__)


@register('save_memory')
def handle_save_memory(ctx):
    obj = resolve_object(ctx.source_type, ctx.source_id, user=ctx.user)
    title = resolve_title(ctx.source_type, obj)
    desc = resolve_description(ctx.source_type, obj)
    from apps.memory.models import TrajectoryEvent
    from django.utils import timezone
    type_map = {'goal':'achievement','content':'learning','message':'reflection','wellness':'learning'}
    event_type = ctx.payload.get('event_type', type_map.get(ctx.source_type, 'learning'))
    ev = TrajectoryEvent.objects.create(user=ctx.user, event_type=event_type,
        title=f'📌 {title[:60]}', description=desc[:500], happened_at=timezone.now())
    logger.info('Created memory %d from %s[%d]', ev.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, message='已保存到记忆', data={'memory_id': ev.pk})
