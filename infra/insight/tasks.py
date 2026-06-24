"""Celery tasks for the insight layer.

Three task families:
1. rebuild_snapshot — event-driven, debounced (countdown=300)
2. refresh_all_snapshots — daily 06:00, cache-warming
3. generate_weekly_reports — weekly Sunday 07:00
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 50  # users per Celery chord chunk


@shared_task(time_limit=120, soft_time_limit=90)
def rebuild_snapshot(user_id):
    """Rebuild InsightSnapshot for a single user (event-driven or batched)."""
    from django.contrib.auth import get_user_model
    from infra.insight.aggregators.insight_snapshot import InsightSnapshot

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        InsightSnapshot(user).build()
        logger.info("Rebuilt insight snapshot for user %d", user_id)
    except User.DoesNotExist:
        logger.warning("User %d not found, skipping snapshot rebuild", user_id)
    except Exception as e:
        logger.error("Failed to rebuild snapshot for user %d: %s", user_id, e)


@shared_task(time_limit=300, soft_time_limit=270)
def refresh_all_snapshots():
    """Rebuild snapshots for all active users (daily cache-warming).

    Distributes users across parallel rebuild_snapshot tasks in chunks
    to avoid blocking a single worker for too long.
    """
    from django.contrib.auth import get_user_model
    from celery import group

    User = get_user_model()
    user_ids = list(
        User.objects.filter(is_active=True).values_list('pk', flat=True)
    )

    if not user_ids:
        logger.info("No active users to refresh snapshots for")
        return "No users"

    # Chunk into groups of _CHUNK_SIZE and dispatch in parallel
    tasks = []
    for i in range(0, len(user_ids), _CHUNK_SIZE):
        chunk = user_ids[i:i + _CHUNK_SIZE]
        tasks.extend(rebuild_snapshot.s(uid) for uid in chunk)  # pyright: ignore[reportCallIssue]

    group(tasks).apply_async()
    logger.info("Dispatched %d snapshot rebuild tasks for %d users", len(tasks), len(user_ids))
    return f"Dispatched {len(tasks)} tasks for {len(user_ids)} users"


@shared_task(time_limit=300, soft_time_limit=270)
def generate_weekly_reports():
    """Generate weekly reports for all active users."""
    from django.contrib.auth import get_user_model
    from celery import group
    from infra.insight.generators.report import ReportGenerator

    User = get_user_model()
    user_ids = list(
        User.objects.filter(is_active=True).values_list('pk', flat=True)
    )

    if not user_ids:
        return "No users"

    tasks = []
    for i in range(0, len(user_ids), _CHUNK_SIZE):
        chunk = user_ids[i:i + _CHUNK_SIZE]
        for uid in chunk:
            tasks.append(_generate_report_for_user.s(uid))  # pyright: ignore[reportCallIssue]

    group(tasks).apply_async()
    logger.info("Dispatched %d report tasks for %d users", len(tasks), len(user_ids))
    return f"Dispatched {len(tasks)} tasks"


@shared_task(time_limit=120, soft_time_limit=90)
def _generate_report_for_user(user_id):
    """Generate a single user's weekly report."""
    from django.contrib.auth import get_user_model
    from infra.insight.generators.report import ReportGenerator

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        ReportGenerator(user).generate("weekly")
    except User.DoesNotExist:
        logger.warning("User %d not found", user_id)
    except Exception as e:
        logger.error("Report failed for user %d: %s", user_id, e)
