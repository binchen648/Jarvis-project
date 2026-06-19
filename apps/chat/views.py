import logging
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from .models import Conversation

logger = logging.getLogger(__name__)


@login_required
def conversation_list(request):
    """列出用户的所有对话."""
    conversations = Conversation.objects.filter(
        user=request.user
    ).annotate(
        msg_count=Count('messages')
    )[:50]
    return render(request, 'chat/conversation_list.html', {
        'conversations': conversations,
    })


@login_required
def conversation_detail(request, pk):
    """单个对话详情（WebSocket 页面）. """
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    history = conversation.messages.all().order_by('created_at')

    # ── Agent State Panel data (for {% include %} in template) ──
    top_goal = None
    today_plan = []
    today_done = 0
    memory_hints = []
    tools_used = []
    suggestions = []
    try:
        from apps.goals.models import Goal, GoalProgress
        active_goals = Goal.objects.filter(
            user=request.user, status='active'
        ).order_by('-created_at')[:5]
        if active_goals.exists():
            best = None
            today = timezone.now().date()
            for g in active_goals:
                if g.deadline and g.deadline >= today:
                    if best is None or g.deadline < best.deadline:
                        best = g
            if best is None:
                best = active_goals.first()
            latest_progress = GoalProgress.objects.filter(
                goal=best
            ).order_by('-recorded_at').first()
            progress_pct = latest_progress.progress_percent if latest_progress else 0.0
            days_left = (best.deadline - today).days if best.deadline else None
            top_goal = {
                'id': best.id,
                'title': best.title,
                'progress': int(progress_pct),
                'days_left': days_left,
                'goal_type': best.get_goal_type_display() if hasattr(best, 'get_goal_type_display') else 'Goal',
                'target_unit': '',
            }
    except Exception:
        pass

    return render(request, 'chat/conversation_detail.html', {
        'conversation': conversation,
        'history': history,
        'top_goal': top_goal,
        'today_plan': today_plan,
        'today_done': today_done,
        'memory_hints': memory_hints,
        'tools_used': tools_used,
        'suggestions': suggestions,
    })


@login_required
def new_conversation(request):
    """创建新对话并跳转."""
    now = timezone.now()
    conv = Conversation.objects.create(
        user=request.user,
        title=f"对话 {now.strftime('%m/%d %H:%M')}",
    )
    return redirect('chat:conversation_detail', pk=conv.pk)


@login_required
def agent_state(request, pk):
    """返回 Agent Active State 面板的 HTML (HTMX 轮询)."""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)

    # ── Top Goal: most recent active goal ─────────────────────────
    top_goal = None
    try:
        from apps.goals.models import Goal, GoalProgress
        active_goals = Goal.objects.filter(
            user=request.user, status='active'
        ).order_by('-created_at')[:5]

        if active_goals.exists():
            best = None
            today = timezone.now().date()
            for g in active_goals:
                if g.deadline and g.deadline >= today:
                    if best is None or g.deadline < best.deadline:
                        best = g
            if best is None:
                best = active_goals.first()

            latest_progress = GoalProgress.objects.filter(
                goal=best
            ).order_by('-recorded_at').first()

            progress_pct = latest_progress.progress_percent if latest_progress else 0.0
            days_left = (best.deadline - today).days if best.deadline else None

            top_goal = {
                'id': best.id,
                'title': best.title,
                'description': best.description[:120] if best.description else '',
                'progress': round(progress_pct, 1),
                'deadline': best.deadline.isoformat() if best.deadline else None,
                'days_left': days_left,
                'goal_type': best.get_goal_type_display(),
                'target_unit': best.target_unit,
            }
    except Exception as exc:
        logger.exception("agent_state top_goal failed: %s", exc)

    # ── Today's Plan: active goals as daily plan items ─────────────
    today_plan = []
    today_done = 0
    try:
        from apps.goals.models import Goal
        active_goals = Goal.objects.filter(
            user=request.user, status='active'
        ).order_by('-created_at')[:3]
        for idx, g in enumerate(active_goals, 1):
            done = False
            try:
                from apps.goals.models import GoalSession
                today = timezone.now().date()
                has_session = GoalSession.objects.filter(
                    user=request.user, goal=g, date=today
                ).exists()
                done = has_session
            except Exception:
                pass
            if done:
                today_done += 1
            today_plan.append({
                'id': idx,
                'title': g.title,
                'done': done,
                'minutes': 30,
            })
    except Exception:
        today_plan = []

    # ── Tools Used: parse from recent assistant messages ───────────
    tools_used = []
    try:
        recent_msgs = conversation.messages.filter(
            role='assistant'
        ).order_by('-created_at')[:10]

        tool_pattern = re.compile(
            r'(?:使用工具|tool_call|调用)\s*[:：]?\s*(\w+)', re.IGNORECASE
        )
        seen_tools = set()
        for msg in recent_msgs:
            matches = tool_pattern.findall(msg.content)
            for tool_name in matches:
                tool_lower = tool_name.lower()
                if tool_lower not in seen_tools:
                    seen_tools.add(tool_lower)
                    tools_used.append({
                        'name': tool_name,
                        'status': 'done',
                        'time': msg.created_at.strftime('%H:%M:%S'),
                    })
            if len(tools_used) >= 5:
                break
    except Exception as exc:
        logger.exception("agent_state tools_used failed: %s", exc)

    # ── Memory Hints: from today's sessions + recent goals ────────
    memory_hints = []
    today_session_count = 0
    try:
        from apps.goals.models import GoalSession
        today = timezone.now().date()
        today_sessions_qs = GoalSession.objects.filter(
            user=request.user, date=today
        ).select_related('goal')
        today_session_count = today_sessions_qs.count()
        today_sessions = today_sessions_qs[:5]

        for session in today_sessions:
            hint = {
                'title': session.goal.title if session.goal else '学习记录',
                'duration': f"{session.duration_minutes}min",
                'note': session.note[:80] if session.note else '',
            }
            memory_hints.append(hint)

        if top_goal:
            memory_hints.insert(0, {
                'title': top_goal['title'],
                'duration': f"{top_goal['progress']}%",
                'note': top_goal.get('description', ''),
            })
    except Exception as exc:
        logger.exception("agent_state memory_hints failed: %s", exc)

    # ── Suggestions: contextual next actions ───────────────────────
    suggestions = []
    try:
        if top_goal and top_goal.get('progress', 0) < 100:
            suggestions.append({
                'text': f"继续推进「{top_goal['title']}」",
                'action': 'continue_goal',
                'goal_id': top_goal['id'],
            })

        if top_goal and top_goal.get('days_left') is not None:
            if top_goal['days_left'] <= 2:
                suggestions.append({
                    'text': f"⚠ 还剩 {top_goal['days_left']} 天截止",
                    'action': 'deadline_alert',
                    'goal_id': top_goal['id'],
                })

        if today_session_count == 0:
            suggestions.append({
                'text': '今天还没有学习记录，开始学习吧',
                'action': 'start_session',
            })

        from apps.goals.models import GoalSession
        today = timezone.now().date()
        three_days_ago = today - timezone.timedelta(days=3)
        recent_session = GoalSession.objects.filter(
            user=request.user, date__gte=three_days_ago
        ).count()
        if recent_session == 0:
            suggestions.append({
                'text': '已 3 天未学习，建议回顾之前的目标',
                'action': 'review_goals',
            })
    except Exception as exc:
        logger.exception("agent_state suggestions failed: %s", exc)

    return render(request, 'chat/agent_state_panel.html', {
        'top_goal': top_goal,
        'tools_used': tools_used,
        'memory_hints': memory_hints,
        'suggestions': suggestions,
        'today_plan': today_plan,
        'today_done': today_done,
    })
