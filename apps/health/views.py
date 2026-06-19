import logging
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """Health check endpoint returning DB and cache status."""
    db_status = "ok"
    redis_status = "unknown"

    # Check PostgreSQL
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError as e:
        logger.warning("Health check DB error: %s", e)
        db_status = "error"

    # Check Redis via Django cache
    try:
        cache.get("__health_check_probe__")
        redis_status = "ok"
    except Exception as e:
        logger.warning("Health check Redis error: %s", e)
        redis_status = "error"

    data = {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "redis": redis_status,
    }

    status_code = 200 if data["status"] == "ok" else 503
    return JsonResponse(data, status=status_code)
