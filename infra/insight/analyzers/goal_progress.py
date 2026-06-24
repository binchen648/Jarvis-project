"""Goal Progress Analyzer — tracks completion, velocity, and stuck detection."""
import logging
from datetime import timedelta
from collections import defaultdict
from django.db.models import Sum, Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class GoalProgressAnalyzer:
    def __init__(self, user):
        self.user = user

    def analyze(self):
        """Analyze all goals for progress, velocity, and stuck status."""
        from apps.goals.models import Goal, GoalProgress, GoalSession

        goals = Goal.objects.filter(user=self.user).order_by('-updated_at')
        now = timezone.now()
        today = timezone.localdate()
        results = []

        for g in goals:
            # Latest progress
            lp = GoalProgress.objects.filter(goal=g).order_by('-recorded_at').first()
            progress = lp.progress_percent if lp else 0.0

            # Previous progress (for velocity calculation)
            pp = GoalProgress.objects.filter(goal=g).order_by('-recorded_at')[1:2].first()
            prev_progress = pp.progress_percent if pp else 0.0

            # Velocity: progress change per day
            days_since_first = 0
            first = GoalProgress.objects.filter(goal=g).order_by('recorded_at').first()
            if first and lp and first.pk != lp.pk:
                days_since_first = max((lp.recorded_at - first.recorded_at).days, 1)

            total_progress_change = progress - prev_progress if prev_progress > 0 else progress
            velocity = round(total_progress_change / max(days_since_first, 1), 2) if days_since_first > 0 else 0.0

            # Days since last update
            days_since_update = (now - (lp.recorded_at if lp else g.created_at)).days

            # Days until deadline
            days_left = (g.deadline - today).days if g.deadline else None

            # Total learning time
            session_agg = GoalSession.objects.filter(goal=g).aggregate(
                total_minutes=Sum('duration_minutes'),
                session_count=Count('pk'),
            )
            total_minutes = session_agg['total_minutes'] or 0
            session_count = session_agg['session_count'] or 0

            # Stuck detection
            stuck_days = days_since_update if g.status == 'active' else 0
            is_stuck = stuck_days >= 14 and progress < 100

            result = {
                'id': g.pk,
                'title': g.title,
                'status': g.status,
                'progress': progress,
                'velocity': velocity,
                'days_since_update': days_since_update,
                'days_left': days_left,
                'total_minutes': total_minutes,
                'session_count': session_count,
                'is_stuck': is_stuck,
                'stuck_days': stuck_days if is_stuck else 0,
            }
            results.append(result)

        return {
            'goals': results,
            'summary': {
                'total': len(results),
                'active': sum(1 for r in results if r['status'] == 'active'),
                'completed': sum(1 for r in results if r['status'] == 'completed'),
                'stuck': sum(1 for r in results if r['is_stuck']),
                'avg_velocity': round(sum(r['velocity'] for r in results) / max(len(results), 1), 2),
                'total_minutes': sum(r['total_minutes'] for r in results),
            },
        }
