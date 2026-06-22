import logging
from ..registry import register, ActionResult

logger = logging.getLogger(__name__)

@register('link')
def handle_link(ctx):
    """Create a RelationEdge between two entities."""
    from ..models import RelationEdge

    target_type = ctx.payload.get('target_type')
    target_id = ctx.payload.get('target_id')
    relation_type = ctx.payload.get('relation_type', 'related')
    note = ctx.payload.get('note', '')

    if not target_type or not target_id:
        return ActionResult(ok=False, message="需要 target_type 和 target_id")

    edge = RelationEdge.objects.create(
        user=ctx.user,
        source_type=ctx.source_type,
        source_id=ctx.source_id,
        target_type=target_type,
        target_id=target_id,
        relation_type=relation_type,
        note=note,
    )
    logger.info("Created relation %s[%d] → %s[%d]",
                ctx.source_type, ctx.source_id, target_type, target_id)
    return ActionResult(ok=True, message="关联已建立", data={"edge_id": edge.pk})
