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
    """GET /api/graph/node/<id> — node + neighbors."""
    from infra.graph.service import GraphService
    svc = GraphService(request.user)
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
