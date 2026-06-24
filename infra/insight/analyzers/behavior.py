"""BehaviorAnalyzer — detects user behavior patterns from session data."""
import logging
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

SHALLOW_MAX = 15
MEDIUM_MAX = 45


class BehaviorAnalyzer:
    """Analyze user learning behavior patterns over a time window.

    Note: active-hours detection is deferred until GoalSession gains a
    timestamp field (currently date is DateField without time).

    Tracks:
    - Session depth distribution (shallow / medium / deep)
    - Daily activity timeline
    - Weekly trend direction
    - Consistency score (active days / total days)
    """

    def __init__(self, user):
        self.user = user

    def analyze(self, days=30):
        from apps.goals.models import GoalSession

        now = timezone.now()
        cutoff = now - timedelta(days=days)

        sessions = list(
            GoalSession.objects.filter(
                user=self.user,
                date__gte=cutoff.date(),
            ).order_by('-date')
        )

        if not sessions:
            return self._empty_result()

        # Session depth distribution
        session_depth: dict[str, int] = {"shallow": 0, "medium": 0, "deep": 0}
        # Daily activity
        daily_map: dict[str, dict] = defaultdict(lambda: {"sessions": 0, "minutes": 0})
        # For weekly trend: track minutes per day
        day_minutes: dict[str, int] = defaultdict(int)

        for s in sessions:
            date_str = s.date.isoformat()
            daily_map[date_str]["sessions"] += 1
            daily_map[date_str]["minutes"] += s.duration_minutes
            day_minutes[date_str] += s.duration_minutes

            # Categorize by session depth
            if s.duration_minutes < SHALLOW_MAX:
                session_depth["shallow"] += 1
            elif s.duration_minutes < MEDIUM_MAX:
                session_depth["medium"] += 1
            else:
                session_depth["deep"] += 1

        # Daily activity sorted
        daily_activity = [
            {"date": d, "sessions": v["sessions"], "minutes": v["minutes"]}
            for d, v in sorted(daily_map.items())
        ]

        # Weekly trend: compare first half vs second half
        sorted_dates = sorted(day_minutes.keys())
        mid = len(sorted_dates) // 2
        if mid == 0:
            weekly_trend = "stable"
        else:
            first_half_avg = sum(day_minutes[d] for d in sorted_dates[:mid]) / mid
            second_half_dates = sorted_dates[mid:]
            second_half_avg = (
                sum(day_minutes[d] for d in second_half_dates) / len(second_half_dates)
                if second_half_dates
                else first_half_avg
            )
            change = second_half_avg - first_half_avg
            if change > 5:
                weekly_trend = "increasing"
            elif change < -5:
                weekly_trend = "declining"
            else:
                weekly_trend = "stable"

        # Consistency score
        total_days = days
        active_days = len(daily_map)
        consistency_score = round(active_days / max(total_days, 1), 2)

        return {
            "session_depth": session_depth,
            "daily_activity": daily_activity,
            "weekly_trend": weekly_trend,
            "consistency_score": consistency_score,
        }

    def _empty_result(self):
        return {
            "session_depth": {"shallow": 0, "medium": 0, "deep": 0},
            "daily_activity": [],
            "weekly_trend": "stable",
            "consistency_score": 0.0,
        }
