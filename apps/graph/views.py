import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@login_required
def graph_page(request):
    """Render the standalone Graph page."""
    return render(request, 'graph/graph.html')


@login_required
def graph_data(request):
    """GET /api/graph/ — root graph."""
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    data = svc.get_root_graph()
    return JsonResponse(data)


@login_required
def graph_node(request, node_id):
    """GET /api/graph/node/<id> — node + neighbors.
    PATCH /api/graph/node/<id> — update node fields.
    DELETE /api/graph/node/<id> — delete node.
    """
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError, TypeError):
            return JsonResponse({'error': 'invalid JSON'}, status=400)
        node = svc.update_node(node_id, **data)
        if node is None:
            return JsonResponse({'error': 'node not found'}, status=404)
        meta = node.metadata or {}
        return JsonResponse({
            'ok': True,
            'node': {
                'id': node.pk,
                'type': node.node_type,
                'title': node.title,
                'description': node.description[:200] if node.description else '',
                'pinned': meta.get('pinned', False),
                'note': meta.get('note', ''),
            }
        })
    
    if request.method == 'DELETE':
        deleted = svc.delete_node(node_id)
        if not deleted:
            return JsonResponse({'error': 'node not found'}, status=404)
        return JsonResponse({'ok': True})
    
    # GET — node + neighbors
    data = svc.get_node_neighbors(node_id)
    return JsonResponse(data)


@login_required
@require_POST
def graph_link(request):
    """POST /api/graph/link — create relation between nodes."""
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)

    from_node = data.get('from_node')
    to_node = data.get('to_node')
    relation = data.get('relation', 'related')

    if not from_node or not to_node:
        return JsonResponse({'error': 'from_node and to_node required'}, status=400)

    edge, created = svc.create_relation(from_node, to_node, relation)
    return JsonResponse({'ok': True, 'edge_id': edge.pk, 'created': created})


@login_required
def graph_unlink(request, edge_id):
    """DELETE /api/graph/link/<id> — remove relation. Accepts POST or DELETE."""
    if request.method not in ('POST', 'DELETE'):
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST', 'DELETE'])
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    deleted = svc.delete_relation(edge_id)
    if not deleted:
        return JsonResponse({'error': 'edge not found'}, status=404)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def graph_link_note(request, edge_id):
    """PATCH /api/graph/link/<id>/note — update edge note."""
    from infra.actions.models import RelationEdge
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    note = data.get('note', '')
    updated = RelationEdge.objects.filter(pk=edge_id, user=request.user).update(note=note)
    if not updated:
        return JsonResponse({'error': 'edge not found'}, status=404)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def graph_link_note_update(request, edge_id):
    """POST /api/graph/link/<id>/ — PATCH update edge fields (note, relation)."""
    from infra.actions.models import RelationEdge
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    edge = RelationEdge.objects.filter(pk=edge_id, user=request.user).first()
    if not edge:
        return JsonResponse({'error': 'edge not found'}, status=404)
    if 'note' in data:
        edge.note = data['note']
    if 'relation' in data:
        edge.relation_type = data['relation']
    edge.save()
    return JsonResponse({'ok': True})


@login_required
def graph_search(request):
    """GET /api/graph/search/?q=xxx — search nodes by title/description."""
    from infra.graph.service import GraphService
    q = request.GET.get('q', '').strip()
    node_type = request.GET.get('type', '')
    if not q and not node_type:
        return JsonResponse({'nodes': [], 'edges': []})
    svc = GraphService(request.user)
    data = svc.search_nodes(q, node_type=node_type, limit=20)
    return JsonResponse(data)


@login_required
@require_POST
def graph_node_create(request):
    """POST /api/graph/node/ — create a new node."""
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    
    title = data.get('title', '').strip()
    node_type = data.get('type', 'goal')
    description = data.get('description', '')
    source_type = data.get('source_type', '')
    source_id = data.get('source_id')
    
    if not title:
        return JsonResponse({'error': 'title is required'}, status=400)
    
    valid_types = ('goal', 'skill', 'interest', 'memory')
    if node_type not in valid_types:
        return JsonResponse({'error': f'type must be one of: {", ".join(valid_types)}'}, status=400)
    
    node = svc.create_node(node_type, title, description=description,
                           source_type=source_type, source_id=source_id)
    meta = node.metadata or {}
    return JsonResponse({
        'ok': True,
        'node': {
            'id': node.pk,
            'type': node.node_type,
            'title': node.title,
            'description': node.description[:200] if node.description else '',
            'importance': node.importance,
            'pinned': meta.get('pinned', False),
            'note': meta.get('note', ''),
        }
    }, status=201)


@login_required
def graph_node_suggestions(request, node_id):
    """GET /api/graph/node/<id>/suggestions — auto-suggest links."""
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
    data = svc.suggest_links(node_id)
    return JsonResponse(data)
