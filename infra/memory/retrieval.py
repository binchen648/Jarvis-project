"""Memory Retrieval — on-demand recall of relevant user context for system prompt injection.

Usage:
    context = retrieve_chat_context(user, page="goals:goal_list")
    # context is a dict ready for system prompt assembly
"""

import logging
from datetime import timedelta
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def retrieve_chat_context(user, page="", conversation_history=None, query=""):
    """Main entry point. Returns compact context dict for system prompt injection.

    Args:
        user: User model instance
        page: Current page URL name (e.g., 'goals:goal_list', 'dashboard:home')
        conversation_history: List of recent messages (optional)

    Returns:
        dict with keys:
        - persona_summary: str (~200 tokens)
        - facts: list of relevant user facts (~100 tokens)
        - interests: list of top interests (~100 tokens)
        - today_context: str (~150 tokens) today's status
        - relevance_hints: str (~50 tokens) for LLM to know what's relevant
    """
    context = {
        'persona_summary': '',
        'facts': [],
        'interests': [],
        'today_context': '',
        'relevance_hints': '',
    }

    # 1. Get persona summary — 优先从 MemoryService 读取 L1/L2
    try:
        from infra.memory.memory_service import get_level1_profile, get_level2_context
        profile = get_level1_profile(user)
        ctx = get_level2_context(user)
        context['persona_summary'] = profile.get('summary', '')
        context['facts'] = list(profile.get('facts', []))[:8]
        context['interests'] = profile.get('interests', [])[:6]
        # 如果 L2 中有今日摘要，优先使用
        if ctx.get('today_summary'):
            context['today_context'] = ctx['today_summary']
    except ImportError:
        # memory_service 不可用，回退到 UserPersona
        try:
            from infra.llm.models import UserPersona
            persona = UserPersona.objects.get(user=user)
            context['persona_summary'] = persona.persona_summary
            facts = persona.facts
            if isinstance(facts, dict):
                # New format: structured dict → flatten to list
                flat = []
                for section in ('goals', 'skills', 'interests'):
                    for item in facts.get(section, [])[:3]:
                        if isinstance(item, dict):
                            flat.append(item.get('title') or item.get('name', ''))
                context['facts'] = flat[:8]
            else:
                context['facts'] = list(facts)[:8]
            context['interests'] = persona.interests[:6]
        except UserPersona.DoesNotExist:
            pass

    # 2. Get today's context（如果 L2 中没有今日摘要，则构建）
    if not context.get('today_context') or context['today_context'] == '':
        context['today_context'] = _build_today_context(user)
    MAX_TODAY_CHARS = 300  # ~150 tokens
    if len(context['today_context']) > MAX_TODAY_CHARS:
        context['today_context'] = context['today_context'][:MAX_TODAY_CHARS] + "…"

    # 3. Get page-specific relevance hints
    context['relevance_hints'] = _get_page_hints(page)

    # 4. Graph RAG context (if query provided)
    context['graph_context'] = []
    if query:
        try:
            from infra.graph.service import GraphService
            svc = GraphService(user)
            context['graph_context'] = svc.retrieve_context(query=query)
        except Exception as e:
            logger.debug("Graph RAG failed: %s", e)

    return context


def _build_today_context(user):
    """Build a compact summary of today's user activity (~150 tokens)."""
    today = timezone.localdate()
    parts = []

    # Today's learning
    try:
        from apps.goals.models import GoalSession
        today_sessions = GoalSession.objects.filter(user=user, date=today)
        total = today_sessions.aggregate(
            models.Sum('duration_minutes')
        )['duration_minutes__sum']
        if total:
            parts.append(f"今日已学{int(total)}分钟")
    except Exception:
        logger.warning("Could not load GoalSession data for user %d", user.pk)

    # Today's wellness
    try:
        from apps.wellness.models import WellnessRecord
        record = WellnessRecord.objects.filter(
            user=user, record_date=today
        ).first()
        if record and record.mood_score:
            mood_map = {1: '很差', 2: '较差', 3: '一般', 4: '良好', 5: '很好'}
            parts.append(f"心情{mood_map.get(record.mood_score, '未知')}")
    except Exception:
        logger.warning("Could not load WellnessRecord data for user %d", user.pk)

    # Active goals count
    try:
        from apps.goals.models import Goal
        active = Goal.objects.filter(user=user, status='active').count()
        if active:
            parts.append(f"进行中目标{active}个")
    except Exception:
        logger.warning("Could not load Goal data for user %d", user.pk)

    return "，".join(parts) if parts else "今日暂无记录"


def _get_page_hints(page):
    """Generate hints about what the user is currently doing based on page."""
    hints = {
        'dashboard:home': '用户刚进入首页，查看全局概况',
        'goals:goal_list': '用户正在查看学习目标列表',
        'goals:goal_detail': '用户正在查看某个目标的详情',
        'goals:goal_create': '用户正在创建新目标',
        'goals:log_session': '用户正在记录学习时长',
        'content:feed': '用户正在浏览推荐内容',
        'content:detail': '用户正在阅读某篇内容',
        'trajectory:skill_graph': '用户正在查看技能图谱',
        'trajectory:path_list': '用户正在查看学习路径',
        'wellness:suggestion_list': '用户正在查看健康建议',
        'wellness:record_create': '用户正在记录身心健康',
        'accounts:profile_detail': '用户正在查看个人资料',
        'accounts:profile_edit': '用户正在编辑个人资料',
        'chat:conversation': '用户在聊天中',
    }
    return hints.get(page, '')


def retrieve_event_stream(user, days=7):
    """Get recent user events for persona builder. Returns structured summaries."""
    from infra.eventbus.models import Event
    since = timezone.now() - timedelta(days=days)
    events = list(
        Event.objects.filter(user=user, created_at__gte=since)
        .order_by('-created_at')[:100]
    )

    summary = {
        'total_events': len(events),
        'by_type': {},
    }
    for e in events:
        summary['by_type'][e.event_type] = (
            summary['by_type'].get(e.event_type, 0) + 1
        )

    return summary


def retrieve_relevant_facts(user, query_topic=None):
    """Retrieve facts relevant to a specific topic.

    优先调用 memory_service.search_memories 进行 FTS5 全文搜索。
    无查询主题时，回退到从 UserPersona 读取。
    """
    # 如果有查询主题，使用 FTS5 搜索
    if query_topic:
        try:
            from infra.memory.memory_service import search_memories
            results = search_memories(user, query_topic, limit=5)
            return [
                r.get('content', '') for r in results
            ]
        except ImportError:
            pass  # 回退到 keyword match
        except Exception:
            logger.warning("memory_service.search_memories failed for user %d", user.pk)

    # 回退：keyword match on stored facts
    try:
        from infra.llm.models import UserPersona
        persona = UserPersona.objects.get(user=user)
        if not query_topic or not persona.facts:
            return persona.facts[:5]
        query_lower = query_topic.lower()
        matched = [
            f
            for f in persona.facts
            if any(word in str(f).lower() for word in query_lower.split())
        ]
        return matched[:5] or persona.facts[:3]
    except UserPersona.DoesNotExist:
        return []
