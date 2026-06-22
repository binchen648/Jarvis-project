"""Action Registry — central dispatch for cross-module actions.

Capabilities define which actions each source type supports.
Handlers are functions that receive ActionContext and return ActionResult.
"""
from dataclasses import dataclass, field
from typing import Optional
from django.http import JsonResponse

CAPABILITIES = {
    "goal":     ["discuss", "make_plan", "save_memory", "link", "create_subgoal"],
    "memory":   ["discuss", "create_goal", "link"],
    "content":  ["discuss", "create_goal", "save_memory", "link"],
    "skill":    ["discuss", "create_goal", "link"],
    "wellness": ["discuss", "link"],
    "message":  ["create_goal", "save_memory", "link"],
}

ACTION_META = {
    "discuss":      {"label": "Discuss with Jarvis", "icon": "brain", "group": "ask"},
    "make_plan":    {"label": "制定计划", "icon": "clipboard", "group": "ask"},
    "save_memory":  {"label": "保存到记忆", "icon": "archive", "group": "save"},
    "create_goal":  {"label": "创建目标", "icon": "target", "group": "save"},
    "link":         {"label": "关联到...", "icon": "link", "group": "connect"},
    "create_subgoal": {"label": "创建子目标", "icon": "git-branch", "group": "save"},
}

HANDLERS = {}

def register(action_id):
    def decorator(func):
        HANDLERS[action_id] = func
        return func
    return decorator


@dataclass
class ActionContext:
    action: str
    source_type: str
    source_id: int
    user: 'User'
    payload: dict = field(default_factory=dict)


@dataclass
class ActionResult:
    ok: bool = True
    redirect: Optional[str] = None
    message: str = ""
    data: dict = field(default_factory=dict)


def get_actions(source_type):
    """Return list of actions available for a source type."""
    action_ids = CAPABILITIES.get(source_type, [])
    result = []
    for aid in action_ids:
        meta = ACTION_META.get(aid, {})
        result.append({
            "id": aid,
            "label": meta.get("label", aid),
            "icon": meta.get("icon", "circle"),
            "group": meta.get("group", "other"),
        })
    return result


def execute(action, source_type, source_id, user, payload=None):
    """Execute an action. Returns ActionResult."""
    handler = HANDLERS.get(action)
    if not handler:
        return ActionResult(ok=False, message=f"Unknown action: {action}")
    ctx = ActionContext(
        action=action,
        source_type=source_type,
        source_id=source_id,
        user=user,
        payload=payload or {},
    )
    return handler(ctx)
