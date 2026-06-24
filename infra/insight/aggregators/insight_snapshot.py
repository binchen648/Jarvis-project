"""InsightSnapshot — cross-analyzer synthesis with caching.

This is the central hub of the insight layer. Consumers (Agent, Dashboard,
Weekly Report, Email, Mobile) all read from the same cached snapshot.
"""
import logging
from datetime import date, datetime, timedelta, timezone

from django.core.cache import cache
from django.utils.timezone import localdate

logger = logging.getLogger(__name__)

SNAPSHOT_TTL = 86400  # 24 hours


class InsightSnapshot:
    """Build a unified snapshot from all analyzers, cached for 24h.

    Cache key pattern: insight:snapshot:{user_id}
    """

    def __init__(self, user):
        self.user = user
        self.cache_key = f"insight:snapshot:{user.pk}"

    def build(self):
        """Return cached snapshot or compute and cache a new one."""
        cached = cache.get(self.cache_key)
        if cached is not None:
            return cached
        snapshot = self._compute()
        try:
            cache.set(self.cache_key, snapshot, SNAPSHOT_TTL)
        except Exception as e:
            logger.warning("Failed to cache snapshot for user %d: %s", self.user.pk, e)
        return snapshot

    def invalidate(self):
        """Force next build() to recompute."""
        cache.delete(self.cache_key)

    # ── Private ──────────────────────────────────────────────────────────

    def _compute(self):
        from infra.insight.analyzers.trend import TrendAnalyzer
        from infra.insight.analyzers.goal_progress import GoalProgressAnalyzer
        from infra.insight.analyzers.behavior import BehaviorAnalyzer

        trend = TrendAnalyzer(self.user).analyze(days=90)
        goals = GoalProgressAnalyzer(self.user).analyze()
        behavior = BehaviorAnalyzer(self.user).analyze(days=30)

        talking_points = self._build_talking_points(trend, goals, behavior)
        engagement = self._build_engagement_signals(behavior, goals)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "top_trends": trend.get("rising", [])[:3],
            "goal_alerts": self._build_goal_alerts(goals),
            "engagement_signals": engagement,
            "identity_changes": [],
            "talking_points": talking_points,
        }

    def _build_talking_points(self, trend, goals, behavior):
        points = []

        # Trending concepts
        for item in trend.get("rising", [])[:3]:
            points.append({
                "type": "trend",
                "title": f"{item['concept']} 关注度上升",
                "summary": (
                    f"{item['concept']} 近期出现 {item['freq_new']} 次，"
                    f"较之前增长 {item['growth_rate']}%"
                ),
            })

        # Stuck goals
        for g in goals.get("goals", []):
            if g.get("is_stuck"):
                points.append({
                    "type": "goal_alert",
                    "title": f"{g['title']} 已停滞 {g['stuck_days']} 天",
                    "summary": (
                        f"目标「{g['title']}」进度 {g['progress']}%，"
                        f"已有 {g['stuck_days']} 天未更新"
                    ),
                })

        # Upcoming deadlines
        for g in goals.get("goals", []):
            dl = g.get("days_left")
            if dl is not None and dl <= 7 and g["progress"] < 100:
                points.append({
                    "type": "deadline",
                    "title": f"{g['title']} 即将截止",
                    "summary": (
                        f"目标「{g['title']}」进度 {g['progress']}%，"
                        f"剩余 {dl} 天"
                    ),
                })

        # Behavior signals
        consistency = behavior.get("consistency_score", 0)
        if consistency > 0.5:
            days = len(behavior.get("daily_activity", []))
            points.append({
                "type": "behavior",
                "title": "保持学习节奏",
                "summary": (
                    f"过去30天中有 {days} 天进行了学习，"
                    f"一致率 {int(consistency * 100)}%"
                ),
            })

        return points

    def _build_goal_alerts(self, goals):
        alerts = []
        for g in goals.get("goals", []):
            if g.get("is_stuck"):
                alerts.append({
                    "goal": g["title"],
                    "status": "stuck",
                    "days": g["stuck_days"],
                })
            dl = g.get("days_left")
            if dl is not None and dl <= 7 and g["progress"] < 100:
                alerts.append({
                    "goal": g["title"],
                    "status": "deadline_approaching",
                    "days": dl,
                })
        return alerts

    def _build_engagement_signals(self, behavior, goals):
        daily = behavior.get("daily_activity", [])
        # Count active days in the last 7 days
        today = localdate()
        cutoff = today - timedelta(days=7)
        weekly_days = sum(
            1
            for entry in daily
            if entry.get("sessions", 0) > 0
            and date.fromisoformat(entry["date"]) >= cutoff
        )
        return {
            "current_streak": self._compute_streak(behavior),
            "weekly_active_days": weekly_days,
            "consistency": behavior.get("consistency_score", 0),
            "trend": behavior.get("weekly_trend", "stable"),
        }

    def _compute_streak(self, behavior):
        """Count consecutive days with sessions, from most recent backwards.

        Compares actual dates to detect gaps — a user active on Jan 1 and
        Jan 30 (but not in between) gets streak=1, not streak=2.
        """
        active_dates = sorted(
            {
                entry["date"]
                for entry in behavior.get("daily_activity", [])
                if entry.get("sessions", 0) > 0
            },
            reverse=True,
        )
        if not active_dates:
            return 0

        today = localdate()
        streak = 0
        expected = today

        for d_str in active_dates:
            d = date.fromisoformat(d_str)
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                break

        return streak
