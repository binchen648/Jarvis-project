from django.db.models.signals import post_save
from django.dispatch import receiver

from .emit import emit_event
from .event_types import (
    CHAT_MESSAGE_SENT,
    GOAL_CREATED,
    GOAL_SESSION_CREATED,
    GOAL_STATUS_CHANGED,
    WELLNESS_RECORDED,
    PATH_NODE_COMPLETED,
)


@receiver(post_save, sender='goals.GoalSession')
def emit_goal_session_created(sender, instance, created, **kwargs):
    """Auto-emit event when a GoalSession is created."""
    if not created:
        return
    emit_event(
        event_type=GOAL_SESSION_CREATED,
        user=instance.user,
        payload={
            'duration_minutes': instance.duration_minutes,
            'goal_id': instance.goal_id,
            'session_id': instance.pk,
        },
    )


@receiver(post_save, sender='wellness.WellnessRecord')
def emit_wellness_recorded(sender, instance, created, **kwargs):
    """Auto-emit event when a WellnessRecord is created."""
    if not created:
        return
    emit_event(
        event_type=WELLNESS_RECORDED,
        user=instance.user,
        payload={
            'mood_score': instance.mood_score,
            'sleep_hours': instance.sleep_hours,
            'record_id': instance.pk,
        },
    )


@receiver(post_save, sender='trajectory.PathNode')
def emit_path_node_completed(sender, instance, **kwargs):
    """Auto-emit event when a PathNode transitions to completed."""
    if instance.status != 'completed':
        return
    emit_event(
        event_type=PATH_NODE_COMPLETED,
        user=instance.path.user,
        payload={
            'path_node_id': instance.pk,
            'path_id': instance.path_id,
            'skill_id': instance.skill_id,
        },
    )


@receiver(post_save, sender='goals.Goal')
def emit_goal_event(sender, instance, created, **kwargs):
    """Emit GOAL_CREATED on new Goal, and GOAL_STATUS_CHANGED on every save."""
    if created:
        emit_event(GOAL_CREATED, user=instance.user, payload={
            'goal_id': instance.pk,
            'title': instance.title,
            'goal_type': instance.goal_type,
        })
    # Always emit status event with current status; consumers deduplicate if needed
    emit_event(GOAL_STATUS_CHANGED, user=instance.user, payload={
        'goal_id': instance.pk,
        'status': instance.status,
    })


@receiver(post_save, sender='chat.Message')
def emit_chat_message(sender, instance, created, **kwargs):
    """Emit CHAT_MESSAGE_SENT only for newly created user messages.

    Note: consumers.py should NOT also emit CHAT_MESSAGE_SENT explicitly,
    since this signal handles it automatically on Message creation.
    """
    if not created:
        return
    if instance.role != 'user':
        return
    emit_event(CHAT_MESSAGE_SENT, user=instance.conversation.user, payload={
        'message_id': instance.pk,
        'conversation_id': instance.conversation_id,
        'content_preview': instance.content[:200],
        'tokens_used': instance.tokens_used,
    })
