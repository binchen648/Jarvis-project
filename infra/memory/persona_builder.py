"""Persona builder — compresses user behavior data into a compact persona summary.

The build process:
1. Collect recent events from Event Store (past 7 days)
2. Collect user interests from Knowledge Graph
3. Collect user skill progress
4. Collect user wellness trends
5. Assemble into a prompt → LLM generates compact summary
6. Update UserPersona

Fallback: No LLM available = rule-based summary from raw data.
"""

import logging
from datetime import timedelta

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def build_persona(user):
    """Build or update persona for a user. Returns UserPersona."""
    from infra.llm.models import UserPersona

    # Collect raw signals
    raw_signals = _collect_signals(user)

    # Generate summary — try LLM first, rule-based fallback
    try:
        from infra.llm.llm_service import summarize_to_persona
        summary = summarize_to_persona(raw_signals)
    except Exception:
        summary = _generate_summary(raw_signals)

    # If LLM returned something empty or too short, fall back
    if not summary or len(summary) < 10:
        summary = _generate_summary(raw_signals)

    # Check if persona already exists to determine version increment
    try:
        existing = UserPersona.objects.get(user=user)
        new_version = existing.version + 1
        created = False
    except UserPersona.DoesNotExist:
        new_version = 1
        created = True

    # Update or create persona
    persona, created = UserPersona.objects.update_or_create(
        user=user,
        defaults={
            'persona_summary': summary,
            'interests': raw_signals.get('interests', []),
            'version': new_version,
            'last_built_at': timezone.now(),
        }
    )

    # 写入 MemoryService（Hermes-inspired 记忆积累）
    try:
        from infra.memory.memory_service import store_memory
        # L1: Persona summary
        store_memory(
            user=user,
            level=1,
            memory_type='persona_summary',
            content=summary,
            metadata={'version': new_version, 'source': 'persona_builder'},
            weight=5.0,
        )
        # L2: Interests
        for interest in raw_signals.get('interests', []):
            store_memory(
                user=user, level=2, memory_type='interest',
                content=interest['tag'],
                metadata={'weight': interest['weight']},
                weight=interest['weight'],
            )
        # L2: Goals
        for goal in raw_signals.get('recent_goals', []):
            store_memory(
                user=user, level=2, memory_type='goal',
                content=goal, weight=3.0,
            )
        # L2: Wellness trend
        if raw_signals.get('mood_trend'):
            avg_mood = sum(raw_signals['mood_trend']) / len(raw_signals['mood_trend'])
            mood_labels = {1: '很差', 2: '较差', 3: '一般', 4: '良好', 5: '很好'}
            store_memory(
                user=user, level=2, memory_type='wellness',
                content=f"近7天心情平均{mood_labels.get(int(avg_mood), '一般')}",
                metadata={'avg_mood': avg_mood, 'trend': raw_signals['mood_trend']},
                weight=2.0,
            )
    except ImportError:
        # memory_service 尚未就绪
        pass
    except Exception as e:
        logger.warning("Failed to store memories after persona build: %s", e)

    return persona


def _collect_signals(user):
    """Collect user behavior signals from all data sources."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    signals = {
        'total_sessions_7d': 0,
        'total_minutes_7d': 0,
        'avg_daily_minutes': 0,
        'active_hours': [],
        'mood_trend': [],
        'interests': [],
        'recent_goals': [],
        'completed_skills': 0,
        'learning_skills': 0,
    }

    # Goals Sessions (past 7 days)
    try:
        from apps.goals.models import GoalSession
        sessions = GoalSession.objects.filter(
            user=user, date__gte=week_ago
        ).select_related('goal')
        for s in sessions:
            signals['total_sessions_7d'] += 1
            signals['total_minutes_7d'] += s.duration_minutes
        if signals['total_sessions_7d'] > 0:
            signals['avg_daily_minutes'] = signals['total_minutes_7d'] / max(signals['total_sessions_7d'], 1)
    except Exception:
        logger.warning("Could not collect GoalSession data for user %d", user.pk)

    # Wellness (past 7 days)
    try:
        from apps.wellness.models import WellnessRecord
        records = WellnessRecord.objects.filter(
            user=user, record_date__gte=week_ago
        )
        signals['mood_trend'] = [r.mood_score for r in records if r.mood_score]
    except Exception:
        logger.warning("Could not collect WellnessRecord data for user %d", user.pk)

    # Interests from Knowledge Graph
    try:
        from apps.trajectory.models import UserInterest
        interests = UserInterest.objects.filter(user=user, weight__gte=0.5)[:10]
        signals['interests'] = [{'tag': i.tag, 'weight': i.weight} for i in interests]
    except Exception:
        logger.warning("Could not collect UserInterest data for user %d", user.pk)

    # Skills
    try:
        from apps.trajectory.models import UserLearningProgress
        progress = UserLearningProgress.objects.filter(user=user)
        signals['completed_skills'] = progress.filter(status='completed').count()
        signals['learning_skills'] = progress.filter(status='learning').count()
    except Exception:
        logger.warning("Could not collect UserLearningProgress data for user %d", user.pk)

    # Recent goals
    try:
        from apps.goals.models import Goal
        goals = Goal.objects.filter(user=user, status='active')[:5]
        signals['recent_goals'] = [g.title for g in goals]
    except Exception:
        logger.warning("Could not collect Goal data for user %d", user.pk)

    return signals


def _generate_summary(signals):
    """Generate a compact persona summary from signals.

    Rule-based fallback when LLM is not available (~200 tokens).
    """
    parts = []

    # Learning pattern
    if signals['avg_daily_minutes'] > 0:
        avg = int(signals['avg_daily_minutes'])
        total = signals['total_minutes_7d']
        parts.append(f"近7天学习{total}分钟，日均{avg}分钟")

    # Active hours
    if signals.get('active_hours'):
        hours = set(signals['active_hours'])
        if hours:
            is_morning = any(6 <= h <= 12 for h in hours)
            is_evening = any(18 <= h <= 23 for h in hours)
            if is_morning and not is_evening:
                parts.append("偏好上午学习")
            elif is_evening and not is_morning:
                parts.append("偏好晚间学习")

    # Interests
    if signals['interests']:
        top = [i['tag'] for i in signals['interests'][:5]]
        parts.append(f"兴趣领域: {', '.join(top)}")

    # Mood/Wellness
    if signals['mood_trend']:
        avg_mood = sum(signals['mood_trend']) / len(signals['mood_trend'])
        if avg_mood >= 4:
            parts.append("近期状态良好")
        elif avg_mood <= 2:
            parts.append("近期状态偏低，可能需要关注")

    # Skills
    if signals['completed_skills'] or signals['learning_skills']:
        parts.append(f"技能进度: 完成{signals['completed_skills']}个，学习中{signals['learning_skills']}个")

    # Goals
    if signals['recent_goals']:
        parts.append(f"当前目标: {'; '.join(signals['recent_goals'][:3])}")

    return "，".join(parts) if parts else "新用户，正在收集学习数据中。"


def get_persona_context(user):
    """Get the full persona context for system prompt injection.

    优先使用 memory_service.get_level1_profile，回退到 UserPersona。
    """
    # 优先尝试 memory_service
    try:
        from infra.memory.memory_service import get_level1_profile
        profile = get_level1_profile(user)
        return {
            'summary': profile.get('summary', ''),
            'facts': list(profile.get('facts', []))[:10],
            'interests': list(profile.get('interests', []))[:8],
        }
    except ImportError:
        pass  # 回退到 UserPersona

    # 回退
    try:
        from infra.llm.models import UserPersona
        persona = UserPersona.objects.get(user=user)
        return {
            'summary': persona.persona_summary,
            'facts': persona.facts[:10],
            'interests': persona.interests[:8],
        }
    except UserPersona.DoesNotExist:
        return {'summary': '', 'facts': [], 'interests': []}
