"""ReportGenerator — formats insight data into consumer-ready reports.

Currently supports weekly reports. Extensible to monthly / daily.
"""
import logging
from datetime import date, timedelta

from django.utils import timezone

from infra.insight.aggregators.insight_snapshot import InsightSnapshot

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Wrap InsightSnapshot into a themed report for a given period."""

    def __init__(self, user):
        self.user = user

    def generate(self, period="weekly"):
        snapshot = InsightSnapshot(self.user).build()
        period_start, period_end = self._period_range(period)

        return {
            "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
            "trends": self._extract_trends(snapshot),
            "goals": self._extract_goals(snapshot),
            "behavior": self._extract_behavior(snapshot),
            "talking_points": snapshot.get("talking_points", []),
            "next_week_focus": self._build_focus(snapshot),
        }

    # ── Private ──────────────────────────────────────────────────────────

    def _period_range(self, period):
        today = timezone.localdate()
        if period == "weekly":
            # Last 7 days (including today)
            return today - timedelta(days=7), today
        elif period == "monthly":
            return today - timedelta(days=30), today
        else:
            return today - timedelta(days=7), today

    def _extract_trends(self, snapshot):
        return {
            "top_rising": snapshot.get("top_trends", []),
            "talking_points": [
                tp for tp in snapshot.get("talking_points", [])
                if tp.get("type") == "trend"
            ],
        }

    def _extract_goals(self, snapshot):
        alerts = snapshot.get("goal_alerts", [])
        return {
            "alerts": alerts,
            "stuck_count": sum(1 for a in alerts if a.get("status") == "stuck"),
            "deadline_count": sum(1 for a in alerts if a.get("status") == "deadline_approaching"),
            "talking_points": [
                tp for tp in snapshot.get("talking_points", [])
                if tp.get("type") in ("goal_alert", "deadline")
            ],
        }

    def _extract_behavior(self, snapshot):
        signals = snapshot.get("engagement_signals", {})
        return {
            "streak": signals.get("current_streak", 0),
            "weekly_active_days": signals.get("weekly_active_days", 0),
            "consistency": signals.get("consistency", 0),
            "trend": signals.get("trend", "stable"),
            "talking_points": [
                tp for tp in snapshot.get("talking_points", [])
                if tp.get("type") == "behavior"
            ],
        }

    def _build_focus(self, snapshot):
        focus = []

        # Stuck goals → revive
        for alert in snapshot.get("goal_alerts", []):
            if alert.get("status") == "stuck":
                focus.append(f"重新关注已停滞的目标：{alert['goal']}")

        # Approaching deadlines
        for alert in snapshot.get("goal_alerts", []):
            if alert.get("status") == "deadline_approaching":
                focus.append(f"完成即将截止的目标：{alert['goal']}（剩余 {alert['days']} 天）")

        # Trending topics → lean in
        for item in snapshot.get("top_trends", []):
            focus.append(f"持续关注热点方向：{item['concept']}")

        if not focus:
            focus.append("回顾本周学习，制定下周计划")

        return focus
