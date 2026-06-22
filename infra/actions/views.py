import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .registry import get_actions, execute

logger = logging.getLogger(__name__)


@login_required
def action_list(request):
    """GET /api/actions/?type=goal → return available actions for type."""
    source_type = request.GET.get('type', '')
    actions = get_actions(source_type)
    return JsonResponse({"actions": actions, "source_type": source_type})


@login_required
@require_POST
def action_execute(request):
    """POST /api/actions/execute → execute an action."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"ok": False, "message": "invalid JSON"}, status=400)

    action = data.get('action', '')
    source = data.get('source', {})
    source_type = source.get('type', '')
    source_id = source.get('id')
    payload = data.get('payload', {})

    if not action or not source_type or not source_id:
        return JsonResponse({"ok": False, "message": "需要 action、source.type、source.id"}, status=400)

    result = execute(action, source_type, source_id, request.user, payload)

    resp = {"ok": result.ok, "message": result.message}
    if result.redirect:
        resp["redirect"] = result.redirect
    if result.data:
        resp["data"] = result.data
    status = 200 if result.ok else 400
    return JsonResponse(resp, status=status)
