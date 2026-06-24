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
import re
from collections import defaultdict
from datetime import timedelta

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def build_persona(user):
    """Build or update persona for a user. Returns UserPersona."""
    from infra.llm.models import UserPersona

    # ── Incremental check ──────────────────────────────────────────
    try:
        persona = UserPersona.objects.get(user=user)
        if persona.last_signal_at is not None:
            latest_signal = _get_last_signal_at(user)
            if latest_signal is not None and latest_signal <= persona.last_signal_at:
                logger.info("Skipping persona build for user %d — no new signals", user.pk)
                return persona
    except UserPersona.DoesNotExist:
        pass

    # ── Collect signals ────────────────────────────────────────────
    raw_signals = _collect_signals(user)

    # ── Generate summary ──────────────────────────────────────────
    try:
        from infra.llm.llm_service import summarize_to_persona
        summary = summarize_to_persona(raw_signals)
    except Exception:
        summary = _generate_summary(raw_signals)
    if not summary or len(summary) < 10:
        summary = _generate_summary(raw_signals)

    # ── Save version history (before updating) ─────────────────────
    try:
        old = UserPersona.objects.get(user=user)
        if old.persona_summary:
            try:
                from infra.memory.memory_service import store_memory
                store_memory(
                    user=user, level=3, memory_type='persona_history',
                    content=old.persona_summary,
                    metadata={
                        'version': old.version,
                        'snapshot_at': timezone.now().isoformat(),
                        'interests': old.interests,
                    },
                    weight=1.0,
                )
            except Exception:
                pass  # memory_service not available, skip history
        new_version = old.version + 1
        created = False
    except UserPersona.DoesNotExist:
        new_version = 1
        created = True

    # ── Get latest signal timestamp ────────────────────────────────
    last_signal = _get_last_signal_at(user)

    # ── Update or create persona ──────────────────────────────────
    persona, created = UserPersona.objects.update_or_create(
        user=user,
        defaults={
            'persona_summary': summary,
            'interests': raw_signals.get('interests', []),
            'facts': raw_signals.get('facts', {}),
            'version': new_version,
            'last_signal_at': last_signal,
            'last_built_at': timezone.now(),
        }
    )

    # ── Store L1/L2 memories ──────────────────────────────────────
    try:
        from infra.memory.memory_service import store_memory
        # L1: Persona summary
        store_memory(
            user=user, level=1, memory_type='persona_summary',
            content=summary, weight=5.0,
            metadata={'version': new_version, 'source': 'persona_builder'},
        )
        # L2: Interests
        for interest in raw_signals.get('interests', []):
            store_memory(
                user=user, level=2, memory_type='interest',
                content=interest['name'],
                metadata={'score': interest['score']},
                weight=interest['score'],
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
        'facts': {},
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

    # L1: Multi-source Interest Scoring
    interest_scores = defaultdict(float)

    # Source 1: Goal tags (extract keywords from title, +3)
    try:
        from apps.goals.models import Goal
        for g in Goal.objects.filter(user=user, status='active'):
            for tag in re.findall(r'[a-zA-Z\u4e00-\u9fff]+', g.title):
                if len(tag) > 1:
                    interest_scores[tag.lower()] += 3.0
    except Exception:
        logger.warning("Could not collect Goal data for interest scoring, user %d", user.pk)

    # Source 2: Skill tags (+2)
    try:
        from apps.trajectory.models import UserLearningProgress, SkillNode
        for p in UserLearningProgress.objects.filter(user=user).select_related('skill'):
            for tag in re.findall(r'[a-zA-Z\u4e00-\u9fff]+', p.skill.name):
                if len(tag) > 1:
                    interest_scores[tag.lower()] += 2.0
    except Exception:
        logger.warning("Could not collect Skill data for interest scoring, user %d", user.pk)

    # Source 3: Content tags (+1)
    try:
        from apps.content.models import ProcessedContent
        for c in ProcessedContent.objects.filter(tags__len__gt=0)[:50]:
            for tag in c.tags:
                if isinstance(tag, str) and len(tag) > 1:
                    interest_scores[tag.lower()] += 1.0
    except Exception:
        logger.warning("Could not collect Content tags for interest scoring, user %d", user.pk)

    # Source 4: UserInterest weight
    try:
        from apps.trajectory.models import UserInterest
        for i in UserInterest.objects.filter(user=user, weight__gte=0.5):
            interest_scores[i.tag.lower()] += float(i.weight)
    except Exception:
        logger.warning("Could not collect UserInterest data for user %d", user.pk)

    # Top 5 sorted
    top_interests = sorted(
        [{"name": name, "score": round(score, 1)} for name, score in interest_scores.items()],
        key=lambda x: -x['score']
    )[:5]

    signals['interests'] = top_interests

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

    # L0: Rule Facts — structured JSON, not natural language
    facts = {"goals": [], "skills": [], "interests": [], "wellness": {}}

    # Goals: Top 5 active
    try:
        from apps.goals.models import Goal
        active_goals = Goal.objects.filter(user=user, status='active').order_by('-updated_at')[:5]
        for g in active_goals:
            facts["goals"].append({"id": g.pk, "title": g.title, "status": g.status})
    except Exception:
        pass

    # Skills: Top 5 completed
    try:
        from apps.trajectory.models import UserLearningProgress, SkillNode
        completed = UserLearningProgress.objects.filter(user=user, status='completed').select_related('skill')[:5]
        for s in completed:
            facts["skills"].append({"id": s.skill_id, "title": s.skill.name, "status": "completed"})
    except Exception:
        pass

    # Wellness: 7-day average mood
    try:
        from apps.wellness.models import WellnessRecord
        from django.db.models import Avg
        cutoff = timezone.now() - timedelta(days=7)
        avg = WellnessRecord.objects.filter(user=user, record_date__gte=cutoff).aggregate(Avg('mood_score'))
        if avg['mood_score__avg']:
            facts["wellness"] = {"avg_mood": round(float(avg['mood_score__avg']), 1), "period_days": 7}
    except Exception:
        pass

    signals['facts'] = facts

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
        top = [i['name'] for i in signals['interests'][:5]]
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


def _get_last_signal_at(user):
    """Get the latest signal timestamp across all data sources."""
    from django.utils import timezone
    latest = None

    # GoalSession (date field — convert to datetime)
    from apps.goals.models import GoalSession as GS
    gs = GS.objects.filter(user=user).order_by('-date').first()
    if gs:
        ts = timezone.make_aware(timezone.datetime.combine(gs.date, timezone.datetime.min.time()))
        if latest is None or ts > latest:
            latest = ts

    # WellnessRecord (record_date field — convert to datetime)
    from apps.wellness.models import WellnessRecord as WR
    wr = WR.objects.filter(user=user).order_by('-record_date').first()
    if wr:
        ts = timezone.make_aware(timezone.datetime.combine(wr.record_date, timezone.datetime.min.time()))
        if latest is None or ts > latest:
            latest = ts

    # UserInterest
    from apps.trajectory.models import UserInterest as UI
    ui = UI.objects.filter(user=user).order_by('-last_updated').first()
    if ui and (latest is None or ui.last_updated > latest):
        latest = ui.last_updated

    # Goal
    from apps.goals.models import Goal as G
    g = G.objects.filter(user=user).order_by('-updated_at').first()
    if g and (latest is None or g.updated_at > latest):
        latest = g.updated_at

    return latest


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
