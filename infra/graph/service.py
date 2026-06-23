"""Graph Service — Universal Graph cognitive layer.

Layers:
  Layer 1 (Cognitive): Goal, Skill, Interest, Memory nodes
  Layer 2 (Evidence): Conversations, Content — not shown directly, available via expand
"""
import logging
from django.utils import timezone
from django.db.models import Count

logger = logging.getLogger(__name__)


class GraphService:
    """Class-based service for the Universal Graph."""
    
    def __init__(self, user):
        self.user = user
    
    def get_root_graph(self):
        """Get the root graph: recent/important nodes + their direct edges."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge
        
        # Layer 1 nodes: active goals + recent memories + skills + interests
        nodes = list(GraphNode.objects.filter(user=self.user).order_by('-importance', '-updated_at')[:50])
        
        node_ids = [n.pk for n in nodes]
        
        # Edges between these nodes
        edges = list(RelationEdge.objects.filter(
            from_node_id__in=node_ids, to_node_id__in=node_ids
        ).select_related('from_node', 'to_node'))
        
        return self._serialize(nodes, edges)
    
    def get_node_neighbors(self, node_id, depth=1):
        """Get a node and its neighbors up to depth steps away (BFS)."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge
        
        try:
            center = GraphNode.objects.get(pk=node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return {'node': None, 'neighbors': [], 'edges': []}
        
        node_set = {center.pk}
        nodes = [center]
        edges = []
        frontier = [center.pk]
        
        for d in range(depth):
            if not frontier:
                break
            next_frontier = []
            outgoing = RelationEdge.objects.filter(from_node_id__in=frontier).select_related('to_node')
            incoming = RelationEdge.objects.filter(to_node_id__in=frontier).select_related('from_node')
            
            for e in outgoing:
                if e.to_node and e.to_node.pk not in node_set:
                    node_set.add(e.to_node.pk)
                    nodes.append(e.to_node)
                    next_frontier.append(e.to_node.pk)
                if e.from_node_id in frontier and e.to_node_id in frontier:
                    edges.append(e)
                elif e.from_node_id in frontier:
                    edges.append(e)
            
            for e in incoming:
                if e.from_node and e.from_node.pk not in node_set:
                    node_set.add(e.from_node.pk)
                    nodes.append(e.from_node)
                    next_frontier.append(e.from_node.pk)
                if e.to_node_id in frontier and e.from_node_id not in node_set:
                    pass  # already handled by outgoing
                elif e.to_node_id in frontier and e.from_node_id not in frontier:
                    edges.append(e)
            
            frontier = next_frontier
        
        return self._serialize(nodes, edges)
    
    def create_node(self, node_type, title, description='', importance=1.0,
                    source_type='', source_id=None):
        """Create a GraphNode."""
        from infra.graph.models import GraphNode
        node = GraphNode.objects.create(
            user=self.user, node_type=node_type, title=title,
            description=description, importance=importance,
            source_type=source_type, source_id=source_id,
        )
        return node
    
    def create_relation(self, from_node_id, to_node_id, relation_type='related'):
        """Create a RelationEdge between two GraphNodes."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge
        from_node = GraphNode.objects.get(pk=from_node_id, user=self.user)
        to_node = GraphNode.objects.get(pk=to_node_id, user=self.user)
        edge, created = RelationEdge.objects.get_or_create(
            user=self.user,
            source_type=from_node.node_type,
            source_id=from_node.pk,
            target_type=to_node.node_type,
            target_id=to_node.pk,
            from_node=from_node,
            to_node=to_node,
            relation_type=relation_type,
        )
        return edge, created
    
    def delete_relation(self, edge_id):
        """Delete a RelationEdge."""
        from infra.actions.models import RelationEdge
        count, _ = RelationEdge.objects.filter(pk=edge_id, user=self.user).delete()
        return count > 0
    
    def _serialize(self, nodes, edges):
        """Serialize nodes and edges to dict format for API."""
        return {
            'nodes': [{
                'id': n.pk,
                'type': n.node_type,
                'title': n.title,
                'description': n.description[:200] if n.description else '',
                'importance': n.importance,
                'source_type': n.source_type,
                'source_id': n.source_id,
            } for n in nodes],
            'edges': [{
                'id': e.pk,
                'source': e.from_node_id,
                'target': e.to_node_id,
                'relation': e.relation_type,
                'weight': getattr(e, 'weight', 1.0),
            } for e in edges if e.from_node_id and e.to_node_id],
        }


# Shorthand for create_node
def create_graph_node(user, node_type, title, **kwargs):
    svc = GraphService(user)
    return svc.create_node(node_type, title, **kwargs)
