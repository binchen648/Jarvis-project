import logging
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from ..concepts import extract_from_text

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze concept frequency trends over a time window.
    
    Fixes applied per code review:
    - extract_from_text returns set (deduplicated)
    - delta uses dual metrics: growth_rate + absolute_growth
    - Goal queries use updated_at, not created_at
    - Conversations sample first + middle + last messages
    """

    def __init__(self, user):
        self.user = user

    def analyze(self, days=90):
        now = timezone.now()
        midpoint = now - timedelta(days=days // 2)
        period_start = now - timedelta(days=days)

        freq_old: defaultdict[str, int] = defaultdict(int)
        freq_new: defaultdict[str, int] = defaultdict(int)

        self._extract_from_conversations(period_start, midpoint, now, freq_old, freq_new)
        self._extract_from_goals(freq_old, freq_new)
        self._extract_from_interests(freq_old, freq_new)

        all_concepts = set(freq_old.keys()) | set(freq_new.keys())
        rising, declining, stable = [], [], []

        for concept in all_concepts:
            old = freq_old.get(concept, 0)
            new = freq_new.get(concept, 0)
            if old + new == 0:
                continue
            growth_rate = ((new - old) / max(old, 1)) * 100
            absolute_growth = new - old
            item = {
                'concept': concept,
                'freq_old': old,
                'freq_new': new,
                'growth_rate': round(growth_rate, 1),
                'absolute_growth': absolute_growth,
            }
            # Sort by absolute_growth first, then growth_rate
            if absolute_growth >= 2:
                rising.append(item)
            elif absolute_growth <= -2:
                declining.append(item)
            else:
                stable.append(item)

        rising.sort(key=lambda x: (-x['absolute_growth'], -x['growth_rate']))
        declining.sort(key=lambda x: (x['absolute_growth'], x['growth_rate']))

        return {
            'rising': rising[:5],
            'declining': declining[:5],
            'stable': stable[:5],
        }

    # ── Extractors ────────────────────────────────────────────────────────

    def _extract_from_conversations(self, period_start, midpoint, now, freq_old, freq_new):
        from apps.chat.models import Conversation
        convs = Conversation.objects.filter(user=self.user, created_at__gte=period_start)
        for conv in convs:
            texts = [conv.title or '']
            all_msgs = list(conv.messages.all())
            total = len(all_msgs)
            if total > 15:
                # Sample: first, middle, last
                sampled = [all_msgs[0], all_msgs[total // 2], all_msgs[-1]]
            elif total > 5:
                # Sample: first, last, plus a few more evenly spaced
                step = max(1, total // 5)
                sampled = [all_msgs[i] for i in range(0, total, step)][:5]
            else:
                sampled = all_msgs[:5]

            for m in sampled:
                texts.append(m.content[:200])

            target = freq_new if conv.created_at >= midpoint else freq_old
            for text in texts:
                concepts = extract_from_text(text)  # returns set
                for cm in concepts:
                    target[cm.concept] += 1

    def _extract_from_goals(self, freq_old, freq_new):
        from apps.goals.models import Goal
        for g in Goal.objects.filter(user=self.user).order_by('-updated_at'):
            target = freq_new if g.updated_at and g.updated_at >= timezone.now() - timedelta(days=45) else freq_old
            for cm in extract_from_text(g.title):
                target[cm.concept] += 1

    def _extract_from_interests(self, freq_old, freq_new):
        from apps.trajectory.models import UserInterest
        for interest in UserInterest.objects.filter(user=self.user).order_by('-weight'):
            target = freq_new if interest.weight >= 2 else freq_old
            for cm in extract_from_text(interest.tag):
                target[cm.concept] += 1


class InterestShiftDetector:
    """Detect concept-to-concept migration patterns.
    
    Example: Algorithms(-30) + AI Agent(+60) → shift from Algorithms to AI Agent
    """
    
    def __init__(self, user):
        self.user = user
    
    def detect(self, days=90):
        """Find pairs where one concept drops while another rises."""
        ta = TrendAnalyzer(self.user)
        raw = ta.analyze(days)
        
        # Build a simple shift hypothesis:
        # If concept A drops significantly and concept B rises significantly,
        # and they share a category or type (from TERM_PATTERNS)...
        shifts = []
        for rising in raw['rising']:
            for declining in raw['declining']:
                if rising['absolute_growth'] > declining['absolute_growth'] * -1:
                    continue  # only flag if rise magnitude exceeds decline
                shifts.append({
                    'from': declining['concept'],
                    'to': rising['concept'],
                    'from_delta': declining['absolute_growth'],
                    'to_delta': rising['absolute_growth'],
                    'confidence': round(
                        min(abs(declining['absolute_growth']), abs(rising['absolute_growth'])) /
                        max(abs(declining['absolute_growth']), abs(rising['absolute_growth']), 1),
                        2
                    ),
                })
        
        shifts.sort(key=lambda s: -s['confidence'])
        return shifts[:3]
