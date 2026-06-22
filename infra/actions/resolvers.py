"""Entity resolvers — unified cross-module entity lookup.

Handlers should NEVER import models directly. Use resolve_object() instead.
"""
import logging
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

# Type → Django Model mapping (lazy imports inside functions)
def _get_model(source_type):
    if source_type == 'goal':
        from apps.goals.models import Goal
        return Goal
    elif source_type == 'memory':
        from apps.memory.models import TrajectoryEvent
        return TrajectoryEvent
    elif source_type == 'content':
        from apps.content.models import ProcessedContent
        return ProcessedContent
    elif source_type == 'skill':
        from apps.trajectory.models import SkillNode
        return SkillNode
    elif source_type == 'wellness':
        from apps.wellness.models import WellnessRecord
        return WellnessRecord
    elif source_type == 'message':
        from apps.chat.models import Message
        return Message
    return None


def resolve_object(source_type, source_id, user=None):
    """Resolve a source_type/source_id pair to a model instance.
    
    Args:
        source_type: String like 'goal', 'memory', 'content'
        source_id: Primary key of the target object
        user: If provided, verifies object.user == user (permission check)
    
    Returns:
        The model instance, or None if type is unknown
    
    Raises:
        Http404 if object doesn't exist
        PermissionDenied if user doesn't own the object (when user is provided)
    """
    Model = _get_model(source_type)
    if Model is None:
        return None
    
    obj = get_object_or_404(Model, pk=source_id)
    
    # Permission check: verify ownership if user is provided
    if user is not None:
        obj_user = getattr(obj, 'user', None)
        if obj_user is not None and obj_user != user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(f"User does not own this {source_type}")
    
    return obj


def resolve_title(source_type, obj):
    """Get a human-readable title from a resolved object."""
    try:
        if hasattr(obj, 'title'):
            return str(obj.title)[:80]
        if hasattr(obj, 'name'):
            return str(obj.name)[:80]
        if hasattr(obj, 'content'):  # Message
            return str(obj.content)[:80]
    except Exception:
        pass
    return f"{source_type}[{obj.pk}]"


def resolve_description(source_type, obj):
    """Get a description/summary from a resolved object."""
    try:
        if hasattr(obj, 'description') and obj.description:
            return str(obj.description)[:500]
        if hasattr(obj, 'content') and obj.content:  # Message
            return str(obj.content)[:500]
    except Exception:
        pass
    return ""
