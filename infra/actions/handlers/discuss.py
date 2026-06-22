import logging
from ..registry import register, ActionResult
from ..resolvers import resolve_object, resolve_title, resolve_description

logger = logging.getLogger(__name__)


@register('discuss')
def handle_discuss(ctx):
    """Create a conversation with the source item as context."""
    obj = resolve_object(ctx.source_type, ctx.source_id, user=ctx.user)
    title = resolve_title(ctx.source_type, obj)
    from apps.chat.models import Conversation, Message
    
    conv = Conversation.objects.create(
        user=ctx.user,
        title=f"讨论: {title[:60]}",
    )
    # Store source metadata so Agent knows the context
    conv.metadata = {
        'source_type': ctx.source_type,
        'source_id': ctx.source_id,
        'source_title': title,
    }
    conv.save(update_fields=['metadata'])
    
    desc = resolve_description(ctx.source_type, obj)
    prompt = f"关于{title}:\n{desc}\n\n请帮我分析并给出建议。"
    Message.objects.create(conversation=conv, role='user', content=prompt)
    
    logger.info("Created conversation %d from %s[%d]", conv.pk, ctx.source_type, ctx.source_id)
    return ActionResult(ok=True, redirect=f"/chat/{conv.pk}/")
