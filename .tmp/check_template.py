import os, sys
sys.path.insert(0, r"D:\Jarvis project")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.demo"
import django
django.setup()
from django.template import loader
from django.template.context import make_context

t = loader.get_template("chat/conversation_detail.html")

class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

ctx = make_context({
    "conversation": MockObj(id=1, title="test"),
    "history": [],
    "top_goal": None,
    "today_plan": [],
    "today_done": 0,
    "memory_hints": [],
    "tools_used": [],
    "suggestions": [],
    "user": MockObj(username="admin", is_authenticated=True),
})
rendered = t.render({
    "conversation": MockObj(id=1, title="test"),
    "history": [],
    "top_goal": None,
    "today_plan": [],
    "today_done": 0,
    "memory_hints": [],
    "tools_used": [],
    "suggestions": [],
    "user": MockObj(username="admin", is_authenticated=True),
})
for c in ["max-width: none", "no-scrollbar", "jarvis-core-sphere", "agent-mode", "Ask", "Plan", "Execute", "deepseek-v3"]:
    status = "OK" if c in rendered else "MISS"
    print(f"  [{status}] {c}")
