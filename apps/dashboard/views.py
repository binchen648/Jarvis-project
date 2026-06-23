from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard 首页 — 展示用户学习概览 (V2 with AI Briefing, KPI, Plan, Timeline)."""

    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        now = timezone.now()

        from apps.goals.models import Goal, GoalSession
        from apps.wellness.models import WellnessRecord, HealthSuggestion
        from apps.trajectory.models import UserLearningProgress

        # ── Goals ────────────────────────────────────────────────────────
        user_goals = Goal.objects.filter(user=user)
        total_goals = user_goals.count()
        completed_goals = user_goals.filter(status="completed").count()
        ctx["total_goals"] = total_goals
        ctx["completed_goals"] = completed_goals

        # ── Goal Sessions (recent 5) ────────────────────────────────────
        ctx["active_goal_sessions"] = GoalSession.objects.filter(user=user).select_related('goal')[:5]

        # ── Wellness ────────────────────────────────────────────────────
        ctx["wellness_today"] = (
            WellnessRecord.objects.filter(user=user, record_date=today).first()
        )
        ctx["unread_suggestions"] = HealthSuggestion.objects.filter(
            user=user, is_read=False
        ).count()

        # ── Skills ──────────────────────────────────────────────────────
        user_progress = UserLearningProgress.objects.filter(user=user)
        ctx["skill_completed"] = user_progress.filter(status="completed").count()
        ctx["skill_in_progress"] = user_progress.filter(status="learning").count()

        # ── Goal Progress Percentage ────────────────────────────────────
        ctx["goal_progress_pct"] = int(completed_goals / total_goals * 100) if total_goals else 0

        # ── Expiring Goals (next 7 days, not completed) ────────────────
        expiring_goals_qs = Goal.objects.filter(
            user=user,
            deadline__gte=today,
            deadline__lte=today + timedelta(days=7),
        ).exclude(status="completed").order_by("deadline")
        expiring_count = expiring_goals_qs.count()
        ctx["expiring_goals"] = expiring_goals_qs[:5]

        # ── Today Learning Minutes ──────────────────────────────────────
        today_total = GoalSession.objects.filter(user=user, date=today).aggregate(
            total=Sum("duration_minutes")
        )["total"]
        ctx["today_learning_minutes"] = today_total or 0

        # ── Weekly Data (last 7 days) ───────────────────────────────────
        WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekly_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_total = GoalSession.objects.filter(
                user=user, date=day
            ).aggregate(total=Sum("duration_minutes"))["total"] or 0
            weekly_data.append({
                "date_label": WEEKDAY_LABELS[day.weekday()],
                "total_minutes": day_total,
            })
        ctx["weekly_data"] = weekly_data

        # ── Health Streak Days ──────────────────────────────────────────
        record_dates = set(
            WellnessRecord.objects.filter(
                user=user,
                record_date__gte=today - timedelta(days=365),
                record_date__lte=today,
            ).values_list("record_date", flat=True)[:366]
        )
        streak = 0
        check_date = today
        while check_date in record_dates:
            streak += 1
            check_date -= timedelta(days=1)
        ctx["health_streak_days"] = streak

        # ── Recent Conversations ────────────────────────────────────────
        from apps.chat.models import Conversation
        ctx["recent_conversations"] = Conversation.objects.filter(
            user=user
        ).order_by("-updated_at")[:3]

        # ── Submitted Today Count ───────────────────────────────────────
        from apps.content.models import UserSubmittedContent
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        ctx["submitted_today_count"] = UserSubmittedContent.objects.filter(
            submitted_by=user, created_at__gte=today_start
        ).count()

        # ── Today Progress Percentage ───────────────────────────────────
        seconds_passed = now.hour * 3600 + now.minute * 60 + now.second
        ctx["today_progress_pct"] = int(seconds_passed / 86400 * 100)

        # =================================================================
        # V2 Context Variables — AI Welcome Briefing, 4 KPI Cards,
        # Today's Plan, Goal Progress Timeline, Memory Timeline
        # =================================================================

        # ── 1. Top Goal (most urgent/important) ──────────────────────────
        ctx["top_goal"] = Goal.objects.filter(
            user=user, status="active"
        ).exclude(deadline__isnull=True).order_by("deadline").first()

        if ctx["top_goal"]:
            goal_sessions = GoalSession.objects.filter(user=user, goal=ctx["top_goal"])
            sess_count = goal_sessions.count()
            if sess_count:
                total_min = goal_sessions.aggregate(
                    total=Sum("duration_minutes")
                )["total"] or 0
                ctx["top_goal_estimated_minutes"] = int(total_min / sess_count)
            else:
                ctx["top_goal_estimated_minutes"] = 30
        else:
            ctx["top_goal_estimated_minutes"] = 30

        # ── 2. AI Suggestion (time-of-day based) ─────────────────────────
        hour = now.hour
        if 5 <= hour < 12:
            ctx["ai_suggestion"] = "上午效率最高，建议先完成最难的目标"
        elif 12 <= hour < 18:
            ctx["ai_suggestion"] = "午后适合复习和整理笔记"
        else:
            ctx["ai_suggestion"] = "今晚适合完成未完成的目标"

        # ── 3. Focus Percentage (KPI) ────────────────────────────────────
        ctx["focus_pct"] = int(completed_goals / max(total_goals, 1) * 100)

        # ── 4. Goal Health (KPI) ─────────────────────────────────────────
        active_count = user_goals.filter(status="active").count()
        ctx["goal_health_normal"] = max(active_count - expiring_count, 0)
        ctx["goal_health_risk"] = expiring_count

        # ── 5. Memory Growth Weekly (KPI) ────────────────────────────────
        try:
            from apps.trajectory.models import TrajectoryEvent
            seven_days_ago = today - timedelta(days=7)
            ctx["memory_growth_weekly"] = TrajectoryEvent.objects.filter(
                user=user, happened_at__gte=seven_days_ago
            ).count()
        except Exception:
            ctx["memory_growth_weekly"] = 0

        # ── 6. AI Confidence Percentage (KPI) ────────────────────────────
        raw_confidence = int(completed_goals / max(total_goals, 1) * 70 + 30)
        ctx["ai_confidence_pct"] = max(70, min(95, raw_confidence))

        # ── 7. Today's Plan Items ────────────────────────────────────────
        today_plan_items = []
        # Build from real active goals with upcoming deadlines
        urgent_goals = user_goals.filter(status="active").exclude(
            deadline__isnull=True
        ).order_by("deadline")[:3]
        for idx, g in enumerate(urgent_goals, 1):
            sess = GoalSession.objects.filter(user=user, goal=g)
            sess_count = sess.count()
            if sess_count:
                total_min = sess.aggregate(
                    total=Sum("duration_minutes")
                )["total"] or 0
                minutes = int(total_min / sess_count)
            else:
                minutes = 30
            days_left = (g.deadline - today).days if g.deadline else 0
            if days_left <= 0:
                desc = "今日截止"
            elif days_left == 1:
                desc = "明天截止"
            else:
                desc = f"截止还有 {days_left} 天"
            today_plan_items.append({
                "id": idx,
                "title": g.title,
                "desc": desc,
                "link": f"/goals/{g.pk}/",
                "done": False,
                "minutes": minutes,
            })

        # Fallback defaults if fewer than 3 real items
        fallback_items = [
            {"title": "LeetCode 92", "desc": "难度 Medium · 今日必完成", "link": "/goals/", "minutes": 35},
            {"title": "阅读 ReAct Agent 笔记", "desc": "上次 3天前 · 需要复习", "link": "/memory/", "minutes": 20},
            {"title": "更新 Wellness 记录", "desc": "", "link": "/wellness/record", "minutes": 5},
        ]
        while len(today_plan_items) < 3:
            fb = fallback_items[len(today_plan_items)]
            today_plan_items.append({
                "id": len(today_plan_items) + 1,
                "title": fb["title"],
                "desc": fb["desc"],
                "link": fb["link"],
                "done": False,
                "minutes": fb["minutes"],
            })
        ctx["today_plan_items"] = today_plan_items

        # ── 8. Goal Progress List (per-goal progress bars) ───────────────
        try:
            from apps.goals.models import GoalProgress
            active_progress_goals = user_goals.filter(status="active")[:5]
            goal_progress_list = []
            for g in active_progress_goals:
                latest = g.progress_records.order_by("-recorded_at").first()
                pct = int(latest.progress_percent) if latest else 0
                goal_progress_list.append({"title": g.title, "pct": pct})
            ctx["goal_progress_list"] = goal_progress_list
        except Exception:
            ctx["goal_progress_list"] = []

        # ── 9. Memory Recent Items (recent entries) ──────────────────────
        try:
            from apps.trajectory.models import TrajectoryEvent
            recent_memories = TrajectoryEvent.objects.filter(
                user=user
            ).order_by("-happened_at")[:5]
            ctx["memory_recent_items"] = [
                {
                    "title": m.title,
                    "description": m.description,
                    "time": m.happened_at,
                }
                for m in recent_memories
            ]
        except Exception:
            ctx["memory_recent_items"] = []

        return ctx


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)


@login_required
@require_POST
def dismiss_surface(request, surface_id):
    """POST /api/surface/<id>/dismiss — soft dismiss."""
    from infra.llm.models import SurfaceEvent
    from infra.surface.service import mark_dismissed
    try:
        event = SurfaceEvent.objects.get(id=surface_id, user=request.user)
        mark_dismissed(event)
        return JsonResponse({"ok": True, "dismissed_id": surface_id})
    except SurfaceEvent.DoesNotExist:
        return JsonResponse({"error": "Surface not found"}, status=404)


@login_required
@require_POST
def mark_surface_read(request, surface_id):
    """POST /api/surfaces/<id>/read — mark surface as read."""
    from infra.llm.models import SurfaceEvent
    from infra.surface.service import mark_read
    try:
        event = SurfaceEvent.objects.get(pk=surface_id, user=request.user)
        changed = mark_read(event)
        return JsonResponse({'ok': True, 'changed': changed})
    except SurfaceEvent.DoesNotExist:
        return JsonResponse({'error': 'Surface not found'}, status=404)


@login_required
@require_POST
def mark_surface_acted(request, surface_id):
    """POST /api/surfaces/<id>/act — mark surface as acted (CTA clicked)."""
    from infra.llm.models import SurfaceEvent
    from infra.surface.service import mark_acted
    try:
        event = SurfaceEvent.objects.get(pk=surface_id, user=request.user)
        mark_acted(event)
        return JsonResponse({'ok': True})
    except SurfaceEvent.DoesNotExist:
        return JsonResponse({'error': 'Surface not found'}, status=404)


@login_required
def core_status(request):
    """API: 返回核心状态数据 (pulse orb state machine)."""
    try:
        import re

        from apps.goals.models import Goal
        from apps.trajectory.models import TrajectoryEvent
        from apps.chat.models import Message
        from django.utils.timesince import timesince

        user = request.user

        active_goals = Goal.objects.filter(user=user, status="active").count()
        memory_count = TrajectoryEvent.objects.filter(user=user).count()

        # Confidence: int (0-99) → float (0.0-1.0)
        raw_confidence = min(50 + active_goals * 5 + memory_count * 3, 99)
        confidence = raw_confidence / 100.0

        # Active tool: most recent tool name from last 10 assistant messages
        active_tool = ""
        tool_pattern = re.compile(
            r'(?:使用工具|tool_call|调用)\s*[:：]?\s*(\w+)', re.IGNORECASE
        )
        recent_msgs = Message.objects.filter(
            conversation__user=user, role="assistant"
        ).order_by("-created_at")[:10]
        for msg in recent_msgs:
            match = tool_pattern.search(msg.content)
            if match:
                active_tool = match.group(1)
                break

        # Last activity: most recent TrajectoryEvent.happened_at
        last_traj = TrajectoryEvent.objects.filter(user=user).order_by("-happened_at").first()
        if last_traj:
            last_activity = timesince(last_traj.happened_at).split(",")[0] + " ago"
        else:
            last_activity = ""

        # Surface stats
        from infra.surface.service import get_stats
        surface_stats = get_stats(user)
        pending_count = surface_stats['pending_count']
        unread_count = surface_stats['unread_count']

        # ── Orb state priority ─────────────────────────────────────────────────
        state = "idle"
        if active_tool:
            state = "executing"
        elif pending_count > 0:
            state = "alert"

        return JsonResponse({
            "state": state,
            "confidence": confidence,
            "memory_count": memory_count,
            "active_tool": active_tool,
            "active_goals": active_goals,
            "pending_count": pending_count,
            "unread_count": unread_count,
            "last_activity": last_activity,
        })
    except Exception as e:
        logger.exception("core_status failed: %s", e)
        return JsonResponse({
            "state": "error",
            "confidence": 0.0,
            "memory_count": 0,
            "active_tool": "",
            "active_goals": 0,
            "pending_count": 0,
            "unread_count": 0,
            "last_activity": "",
        })


@login_required
def surface_list(request):
    """GET /api/surfaces/ — return pending + read surfaces."""
    from infra.surface.service import get_pending_surfaces
    events = get_pending_surfaces(request.user)
    data = []
    for se in events:
        data.append({
            'id': se.pk,
            'type': se.event_type,
            'priority': se.priority,
            'title': se.title,
            'description': se.description or '',
            'status': se.status,
            'source': {'type': se.source_type, 'id': se.source_id} if se.source_type else None,
            'cta': se.payload.get('cta', {'action': 'discuss', 'label': '查看', 'icon': 'stars'}),
        })
    return JsonResponse({'surfaces': data, 'count': len(data)})


@login_required
def dashboard_layout(request):
    """GET: return layout_config. POST: save layout_config."""
    from apps.dashboard.models import DashboardLayout
    from django.http import JsonResponse

    if request.method == 'GET':
        layout, _ = DashboardLayout.objects.get_or_create(user=request.user)
        return JsonResponse({'layout_config': layout.layout_config})

    elif request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError, TypeError):
            return JsonResponse({'error': 'invalid JSON'}, status=400)

        new_config = data.get('layout_config')
        if new_config is None:
            return JsonResponse({'error': 'layout_config required'}, status=400)

        layout, _ = DashboardLayout.objects.get_or_create(user=request.user)
        layout.layout_config = new_config
        layout.save(update_fields=['layout_config'])
        return JsonResponse({'ok': True, 'layout_config': layout.layout_config})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
