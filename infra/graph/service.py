"""Graph Service — Universal Graph cognitive layer.

Layers:
  Layer 1 (Cognitive): Goal, Skill, Interest, Memory nodes
  Layer 2 (Evidence): Conversations, Content — not shown directly, available via expand
"""
import logging
from django import db as django_db
from django.utils import timezone
from django.db.models import Count, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce

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
            outgoing = RelationEdge.objects.filter(from_node_id__in=frontier, user=self.user).select_related('to_node')
            incoming = RelationEdge.objects.filter(to_node_id__in=frontier, user=self.user).select_related('from_node')
            
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
    
    def update_node(self, node_id, **kwargs):
        """Update a GraphNode's metadata fields (pinned, note, color, etc.)."""
        from infra.graph.models import GraphNode
        try:
            node = GraphNode.objects.get(pk=node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return None
        
        # Store pinned/note in metadata JSONField
        meta = dict(node.metadata or {})
        for key in ('pinned', 'note', 'color', 'importance'):
            if key in kwargs:
                if key in ('pinned', 'note', 'color'):
                    meta[key] = kwargs[key]
                else:
                    setattr(node, key, kwargs[key])
        
        node.metadata = meta
        node.save()
        return node
    
    def delete_node(self, node_id):
        """Delete a GraphNode (user must own it)."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge
        try:
            node = GraphNode.objects.get(pk=node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return False
        # Also remove edges involving this node
        Q = django_db.models.Q
        RelationEdge.objects.filter(
            Q(from_node=node) | Q(to_node=node),
            user=self.user
        ).delete()
        node.delete()
        return True
    
    def delete_relation(self, edge_id):
        """Delete a RelationEdge."""
        from infra.actions.models import RelationEdge
        count, _ = RelationEdge.objects.filter(pk=edge_id, user=self.user).delete()
        return count > 0

    def retrieve_context(self, query: str = "", limit: int = 5) -> list[dict]:
        """Graph RAG: match nodes by keyword against user query.
        
        Extracts keywords from query, scores nodes by keyword overlap × importance.
        Returns top N nodes for system prompt injection.
        """
        import re
        from infra.graph.models import GraphNode
        
        if not query or not query.strip():
            return []
        
        keywords = set(re.findall(r'[a-zA-Z\u4e00-\u9fff]+', query.lower()))
        keywords = {k for k in keywords if len(k) > 1}  # filter single chars
        
        if not keywords:
            return []
        
        # DB-side pre-filter: only fetch nodes matching any keyword
        from infra.graph.models import GraphNode
        q = django_db.models.Q(user=self.user)
        for kw in keywords:
            q |= django_db.models.Q(title__icontains=kw) | django_db.models.Q(description__icontains=kw)

        scored = []
        for n in GraphNode.objects.filter(q).only('pk', 'title', 'description', 'node_type', 'importance'):
            text = (n.title + ' ' + (n.description or '')).lower()
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                score = (matches / len(keywords)) * min(n.importance or 1.0, 3.0)
                scored.append({
                    'id': n.pk, 'title': n.title, 'type': n.node_type,
                    'score': round(score, 2),
                })
        
        scored.sort(key=lambda x: -x['score'])
        return scored[:limit]

    def search_nodes(self, query: str, node_type: str = "", limit: int = 10) -> dict:
        """Keyword search on node titles and descriptions."""
        from infra.graph.models import GraphNode

        Q = django_db.models.Q
        q = Q(user=self.user) & (Q(title__icontains=query) | Q(description__icontains=query))
        if node_type:
            q &= Q(node_type=node_type)

        nodes = list(
            GraphNode.objects.filter(q).order_by('-importance', '-updated_at')[:limit]
        )
        return self._serialize(nodes, [])

    def find_paths(self, from_node_id: int, to_node_id: int, max_depth: int = 5) -> dict:
        """BFS shortest path between two nodes. Returns list of paths with nodes and edges."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge
        from collections import deque

        try:
            GraphNode.objects.get(pk=from_node_id, user=self.user)
            GraphNode.objects.get(pk=to_node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return {'nodes': [], 'edges': [], 'paths': [], 'error': '节点不存在'}

        # BFS to find shortest path
        visited = {from_node_id: (None, None)}  # node_id -> (parent_id, edge_id)
        queue = deque([from_node_id])
        found = False
        remaining_depth = max_depth

        while queue and remaining_depth > 0:
            remaining_depth -= 1
            level_size = len(queue)
            for _ in range(level_size):
                current = queue.popleft()
                if current == to_node_id:
                    found = True
                    break

                # Outgoing edges
                for e in RelationEdge.objects.filter(from_node_id=current, user=self.user).select_related('to_node'):
                    if e.to_node_id not in visited and e.to_node_id is not None:
                        visited[e.to_node_id] = (current, e.pk)
                        queue.append(e.to_node_id)

                # Incoming edges
                for e in RelationEdge.objects.filter(to_node_id=current, user=self.user).select_related('from_node'):
                    if e.from_node_id not in visited and e.from_node_id is not None:
                        visited[e.from_node_id] = (current, e.pk)
                        queue.append(e.from_node_id)

            if found:
                break

        if not found:
            return {'nodes': [], 'edges': [], 'paths': [], 'error': '未找到路径'}

        # Reconstruct path
        path_node_ids = []
        path_edge_ids = []
        current = to_node_id
        while current is not None:
            path_node_ids.append(current)
            parent, edge_id = visited[current]
            if edge_id is not None:
                path_edge_ids.append(edge_id)
            current = parent
        path_node_ids.reverse()
        path_edge_ids.reverse()

        all_nodes = list(GraphNode.objects.filter(pk__in=path_node_ids, user=self.user))
        all_edges = list(RelationEdge.objects.filter(pk__in=path_edge_ids, user=self.user))

        result = self._serialize(all_nodes, all_edges)
        result['paths'] = [[n.pk for n in all_nodes]]
        return result

    def get_related_subgraph(self, node_id: int, depth: int = 2, relation_types: list[str] = None) -> dict:
        """Get a subgraph centered on a node, expanding up to depth steps.
        Optionally filter by relation types."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge

        try:
            center = GraphNode.objects.get(pk=node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return {'nodes': [], 'edges': [], 'error': '节点不存在'}

        node_set = {center.pk}
        nodes = [center]
        edges = []
        frontier = [center.pk]

        edge_filter = {}
        if relation_types:
            edge_filter['relation_type__in'] = relation_types

        for d in range(depth):
            if not frontier:
                break
            next_frontier = []

            outgoing = RelationEdge.objects.filter(
                from_node_id__in=frontier, **edge_filter
            ).select_related('to_node')
            incoming = RelationEdge.objects.filter(
                to_node_id__in=frontier, **edge_filter
            ).select_related('from_node')

            for e in outgoing:
                if e.to_node and e.to_node.pk not in node_set and e.to_node.user_id == self.user.pk:
                    node_set.add(e.to_node.pk)
                    nodes.append(e.to_node)
                    next_frontier.append(e.to_node.pk)
                if e.from_node_id in frontier and e.to_node_id in frontier:
                    if e not in edges:
                        edges.append(e)
                elif e.from_node_id in frontier:
                    if e not in edges:
                        edges.append(e)

            for e in incoming:
                if e.from_node and e.from_node.pk not in node_set and e.from_node.user_id == self.user.pk:
                    node_set.add(e.from_node.pk)
                    nodes.append(e.from_node)
                    next_frontier.append(e.from_node.pk)
                if e.to_node_id in frontier and e.from_node_id not in node_set:
                    pass
                elif e.to_node_id in frontier and e.from_node_id not in frontier:
                    if e not in edges:
                        edges.append(e)

            frontier = next_frontier

        result = self._serialize(nodes, edges)
        result['center_id'] = node_id
        result['depth'] = depth
        return result

    def suggest_links(self, node_id: int, limit: int = 5) -> dict:
        """Suggest nodes that might be related to the given node.
        
        Strategy (simple, no ML):
        1. Find nodes with shared keywords in title (split by common delimiters)
        2. Find nodes of the same type with high importance
        3. Find nodes connected to common neighbors (2-hop overlap)
        4. Score and rank by relevance
        
        Returns: {"suggestions": [{"node": {...}, "score": float, "reason": str}]}
        """
        from infra.graph.models import GraphNode
        import re
        from collections import Counter
        
        try:
            center = GraphNode.objects.get(pk=node_id, user=self.user)
        except GraphNode.DoesNotExist:
            return {"suggestions": []}
        
        # Extract keywords from title
        keywords = set(re.findall(r'[a-zA-Z\u4e00-\u9fff]+', center.title.lower()))
        keywords.discard('')  # remove empty strings
        
        suggestions = []
        scored = {}  # node_id -> score
        
        # Strategy 1: Shared keywords in title
        if keywords:
            for n in GraphNode.objects.filter(user=self.user).exclude(pk=node_id):
                title_lower = n.title.lower()
                matches = sum(1 for kw in keywords if kw in title_lower)
                if matches > 0:
                    score = matches / max(len(keywords), 1) * 0.5  # max 0.5 from keywords
                    scored[n.pk] = scored.get(n.pk, 0) + score
        
        # Strategy 2: Same type, high importance
        for n in GraphNode.objects.filter(
            user=self.user, node_type=center.node_type
        ).exclude(pk=node_id).order_by('-importance')[:5]:
            score = (n.importance / 3.0) * 0.3  # max 0.3 from importance
            scored[n.pk] = scored.get(n.pk, 0) + score
        
        # Strategy 3: Common neighbors (2-hop overlap)
        from infra.actions.models import RelationEdge
        center_neighbors = set(
            RelationEdge.objects.filter(
                from_node=center, user=self.user
            ).values_list('to_node_id', flat=True)
        ) | set(
            RelationEdge.objects.filter(
                to_node=center, user=self.user
            ).values_list('from_node_id', flat=True)
        )
        
        if center_neighbors:
            # For each neighbor, find their neighbors
            center_neighbors = {n for n in center_neighbors if n is not None}
            for nid in center_neighbors:
                neighbor_edges = RelationEdge.objects.filter(
                    from_node_id=nid, user=self.user
                ).exclude(to_node_id=node_id)
                for e in neighbor_edges:
                    if e.to_node_id and e.to_node_id not in center_neighbors:
                        scored[e.to_node_id] = scored.get(e.to_node_id, 0) + 0.2
            
            neighbor_incoming = RelationEdge.objects.filter(
                to_node_id__in=center_neighbors, user=self.user
            ).exclude(from_node_id=node_id)
            for e in neighbor_incoming:
                if e.from_node_id and e.from_node_id not in center_neighbors:
                    scored[e.from_node_id] = scored.get(e.from_node_id, 0) + 0.2
        
        # Build results
        for nid, score in scored.items():
            if score < 0.1:  # threshold
                continue
            try:
                n = GraphNode.objects.get(pk=nid, user=self.user)
            except GraphNode.DoesNotExist:
                continue
            # Determine reason
            reason = "关键词匹配" if score >= 0.3 else "同类型节点" if score >= 0.2 else "间接关联"
            suggestions.append({
                "node": {
                    "id": n.pk,
                    "title": n.title,
                    "type": n.node_type,
                },
                "score": round(min(score, 1.0), 2),
                "reason": reason,
            })
        
        suggestions.sort(key=lambda s: -s['score'])
        return {"suggestions": suggestions[:limit]}

    def get_graph_statistics(self) -> dict:
        """Aggregate stats: total nodes by type, total edges by relation type, most connected nodes."""
        from infra.graph.models import GraphNode
        from infra.actions.models import RelationEdge

        # Nodes by type
        nodes_by_type = dict(
            GraphNode.objects.filter(user=self.user)
            .values('node_type')
            .annotate(count=Count('id'))
            .order_by('-count')
            .values_list('node_type', 'count')
        )

        # Edges by relation type
        edges_by_type = dict(
            RelationEdge.objects.filter(user=self.user)
            .values('relation_type')
            .annotate(count=Count('id'))
            .order_by('-count')
            .values_list('relation_type', 'count')
        )

        # Most connected nodes (by total edge count)
        # Uses Subquery to avoid COUNT multiplication from multiple LEFT JOINs
        out_q = RelationEdge.objects.filter(
            from_node=OuterRef('pk'), user=self.user
        ).order_by().values('from_node').annotate(c=Count('*')).values('c')
        in_q = RelationEdge.objects.filter(
            to_node=OuterRef('pk'), user=self.user
        ).order_by().values('to_node').annotate(c=Count('*')).values('c')

        most_connected = (
            GraphNode.objects.filter(user=self.user)
            .annotate(
                out_cnt=Subquery(out_q, output_field=IntegerField()),
                in_cnt=Subquery(in_q, output_field=IntegerField()),
                edge_count=Coalesce('out_cnt', 0) + Coalesce('in_cnt', 0),
            )
            .order_by('-edge_count')[:10]
            .values('pk', 'node_type', 'title', 'edge_count')
        )

        return {
            'total_nodes': sum(nodes_by_type.values()),
            'total_edges': sum(edges_by_type.values()),
            'nodes_by_type': nodes_by_type,
            'edges_by_type': edges_by_type,
            'most_connected': list(most_connected),
        }

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
                'pinned': (n.metadata or {}).get('pinned', False),
                'note': (n.metadata or {}).get('note', ''),
            } for n in nodes],
            'edges': [{
                'id': e.pk,
                'source': e.from_node_id,
                'target': e.to_node_id,
                'relation': e.relation_type,
                'note': e.note or '',
                'weight': getattr(e, 'weight', 1.0),
            } for e in edges if e.from_node_id and e.to_node_id],
        }


# Shorthand for create_node
def create_graph_node(user, node_type, title, **kwargs):
    svc = GraphService(user)
    return svc.create_node(node_type, title, **kwargs)
