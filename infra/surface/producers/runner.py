"""Run all producers for a user."""
import logging
from . import goal, memory, wellness, agent

logger = logging.getLogger(__name__)

PRODUCERS = [goal, memory, wellness, agent]

def run_all(user):
    """Run all producers and return total created events."""
    total = 0
    for producer in PRODUCERS:
        try:
            total += producer.produce(user)
        except Exception as e:
            logger.error('Producer %s failed for user %d: %s', producer.__name__, user.pk, e)
    logger.info('All producers: created %d total events for user %d', total, user.pk)
    return total
