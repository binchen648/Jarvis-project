"""Project status skill — scans the project and reports current state."""
from django.utils import timezone
from django.db.models import Sum
from ..registry import BaseSkill, skill_registry


class ProjectStatusSkill(BaseSkill):
    name = "project_status"
    description = "查看看 Jarvis OS 当前的项目状态：用户数据概况、活跃目标、记忆数、对话数、系统健康度。调用此工具获取用户学习状态的全局快照。"
    parameters = {
        "type": "object",
        "properties": {},
    }
    
    def run(self, user, **kwargs):
        from django.db import connection
        
        report = {
            "timestamp": timezone.now().isoformat(),
            "sections": {},
        }
        
        # User stats
        report["sections"]["user"] = {
            "username": user.username,
            "joined": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
        }
        
        # Goals
        try:
            from apps.goals.models import Goal, GoalSession
            active = Goal.objects.filter(user=user, status='active').count()
            completed = Goal.objects.filter(user=user, status='completed').count()
            total = Goal.objects.filter(user=user).count()
            today_minutes = GoalSession.objects.filter(
                user=user, date=timezone.localdate()
            ).aggregate(total=Sum('duration_minutes'))['total__sum'] or 0
            report["sections"]["goals"] = {
                "active": active, "completed": completed, "total": total,
                "today_minutes": today_minutes,
            }
        except Exception as e:
            report["sections"]["goals"] = {"error": str(e)}
        
        # Memory
        try:
            from apps.memory.models import TrajectoryEvent
            total_mem = TrajectoryEvent.objects.filter(user=user).count()
            week_ago = timezone.now() - timezone.timedelta(days=7)
            recent_mem = TrajectoryEvent.objects.filter(user=user, happened_at__gte=week_ago).count()
            report["sections"]["memory"] = {
                "total": total_mem, "recent_7d": recent_mem,
            }
        except Exception as e:
            report["sections"]["memory"] = {"error": str(e)}
        
        # Conversations
        try:
            from apps.chat.models import Conversation, Message
            conv_count = Conversation.objects.filter(user=user).count()
            msg_count = Message.objects.filter(conversation__user=user).count()
            report["sections"]["chat"] = {
                "conversations": conv_count, "messages": msg_count,
            }
        except Exception as e:
            report["sections"]["chat"] = {"error": str(e)}
        
        # Wellness
        try:
            from apps.wellness.models import WellnessRecord
            today_rec = WellnessRecord.objects.filter(user=user, record_date=timezone.localdate()).first()
            report["sections"]["wellness"] = {
                "has_today_record": today_rec is not None,
                "mood": today_rec.mood_score if today_rec else None,
            }
        except Exception as e:
            report["sections"]["wellness"] = {"error": str(e)}
        
        # Knowledge graph
        try:
            from infra.actions.models import RelationEdge
            edge_count = RelationEdge.objects.filter(user=user).count()
            report["sections"]["graph"] = {"relations": edge_count}
        except Exception:
            report["sections"]["graph"] = {"relations": 0}
        
        # Pending surfaces
        try:
            from infra.llm.models import SurfaceEvent
            pending = SurfaceEvent.objects.filter(user=user, status='pending').count()
            report["sections"]["surfaces"] = {"pending": pending}
        except Exception:
            report["sections"]["surfaces"] = {"pending": 0}
        
        report["summary"] = self._summarize(report["sections"])
        return report
    
    def _summarize(self, sections):
        parts = []
        g = sections.get("goals", {})
        if "error" not in g:
            if g["active"]:
                parts.append(f"有 {g['active']} 个活跃目标，今日学习 {g['today_minutes']} 分钟")
            else:
                parts.append("暂无活跃目标")
        m = sections.get("memory", {})
        if "error" not in m:
            parts.append(f"累计 {m['total']} 条记忆，近 7 天新增 {m['recent_7d']} 条")
        return "；".join(parts)


# Auto-register on module import
skill_registry.register(ProjectStatusSkill)
