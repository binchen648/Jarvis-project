import logging
from ..registry import register, ActionResult
from ..resolvers import resolve_object

logger = logging.getLogger(__name__)


@register('link')
def handle_link(ctx):
    from ..models import RelationEdge
    # Resolve source (with permission check)
    resolve_object(ctx.source_type, ctx.source_id, user=ctx.user)
    # Resolve target (with permission check)
    target_type = ctx.payload.get('target_type')
    target_id = ctx.payload.get('target_id')
    if not target_type or not target_id:
        return ActionResult(ok=False, message='需要 target_type 和 target_id')
    resolve_object(target_type, target_id, user=ctx.user)
    # Create or get existing edge
    edge, created = RelationEdge.objects.get_or_create(
        user=ctx.user,
        source_type=ctx.source_type,
        source_id=ctx.source_id,
        target_type=target_type,
        target_id=target_id,
        relation_type=ctx.payload.get('relation_type', 'related'),
        defaults={'note': ctx.payload.get('note', '')},
    )
    action = 'Created' if created else 'Already exists'
    logger.info('%s relation %s[%d] -> %s[%d]', action, ctx.source_type, ctx.source_id, target_type, target_id)
    msg = '关联已建立' if created else '关联已存在'
    return ActionResult(ok=True, message=msg, data={'edge_id': edge.pk, 'created': created})
