import logging
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from ..concepts import extract_from_text

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze concept frequency trends over a time window."""

    def __init__(self, user):
        self.user = user

    def analyze(self, days=90):
        """Return rising / declining / stable concepts for the last *days*.

        Returns a dict with three keys (*rising*, *declining*, *stable*),
        each containing up to 5 items sorted by magnitude.
        """
        now = timezone.now()
        midpoint = now - timedelta(days=days // 2)
        period_start = now - timedelta(days=days)

        freq_old: defaultdict[str, int] = defaultdict(int)
        freq_new: defaultdict[str, int] = defaultdict(int)

        self._extract_from_conversations(period_start, midpoint, now, freq_old, freq_new)
        self._extract_from_goals(freq_old, freq_new)
        self._extract_from_interests(freq_old, freq_new)

        all_concepts = set(freq_old.keys()) | set(freq_new.keys())
        rising: list[dict] = []
        declining: list[dict] = []
        stable: list[dict] = []

        for concept in all_concepts:
            old = freq_old.get(concept, 0)
            new = freq_new.get(concept, 0)
            if old + new == 0:
                continue
            delta_pct = ((new - old) / max(old, 1)) * 100
            item = {
                'concept': concept,
                'freq_old': old,
                'freq_new': new,
                'delta_pct': round(delta_pct, 1),
            }
            if delta_pct > 30:
                rising.append(item)
            elif delta_pct < -30:
                declining.append(item)
            else:
                stable.append(item)

        rising.sort(key=lambda x: -x['delta_pct'])
        declining.sort(key=lambda x: x['delta_pct'])

        return {
            'rising': rising[:5],
            'declining': declining[:5],
            'stable': stable[:5],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_from_conversations(
        self,
        period_start,
        midpoint,
        now,
        freq_old: defaultdict[str, int],
        freq_new: defaultdict[str, int],
    ):
        from apps.chat.models import Conversation

        convs = Conversation.objects.filter(
            user=self.user, created_at__gte=period_start
        )
        for conv in convs:
            texts = [conv.title or '']
            for m in conv.messages.all()[:5]:
                texts.append(m.content[:200])

            for text in texts:
                concepts = extract_from_text(text)
                target = freq_new if conv.created_at >= midpoint else freq_old
                for cm in concepts:
                    target[cm.concept] += 1

    def _extract_from_goals(
        self,
        freq_old: defaultdict[str, int],
        freq_new: defaultdict[str, int],
    ):
        from apps.goals.models import Goal

        for i, g in enumerate(
            Goal.objects.filter(user=self.user).order_by('-created_at')
        ):
            target = freq_new if i < 3 else freq_old
            for cm in extract_from_text(g.title):
                target[cm.concept] += 1

    def _extract_from_interests(
        self,
        freq_old: defaultdict[str, int],
        freq_new: defaultdict[str, int],
    ):
        from apps.trajectory.models import UserInterest

        for i, interest in enumerate(
            UserInterest.objects.filter(user=self.user).order_by('-weight')
        ):
            target = freq_new if i < 3 else freq_old
            for cm in extract_from_text(interest.tag):
                target[cm.concept] += 1
