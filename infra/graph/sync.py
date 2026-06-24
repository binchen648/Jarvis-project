"""Graph sync — auto-create/update GraphNodes when source data changes."""
import logging

logger = logging.getLogger(__name__)


def sync_goal_to_graph(goal):
    """Create or update a GraphNode for a Goal.

    - If node with source_type='goal', source_id=goal.pk exists → update
    - If not → create new
    - Only sync if goal is active or completed (skip draft/deleted)
    """
    from infra.graph.models import GraphNode

    if goal.status not in ('active', 'completed'):
        return None

    node, created = GraphNode.objects.update_or_create(
        user=goal.user,
        source_type='goal',
        source_id=goal.pk,
        defaults={
            'node_type': 'goal',
            'title': goal.title,
            'description': goal.description or '',
            'importance': _goal_importance(goal),
        }
    )
    logger.debug("%s GraphNode for goal %d", "Created" if created else "Updated", goal.pk)
    return node


def _goal_importance(goal):
    """Calculate node importance based on goal status and deadline."""
    base = 1.0
    if goal.status == 'completed':
        base = 0.8
    if goal.deadline:
        from django.utils import timezone
        days_left = (goal.deadline - timezone.localdate()).days
        if days_left is not None and days_left < 7:
            base += 0.5  # urgent → higher importance
    return min(base, 3.0)
