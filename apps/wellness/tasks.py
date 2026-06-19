import logging
from datetime import timedelta
from django.db import models
from django.utils import timezone
from celery import shared_task

logger = logging.getLogger(__name__)

BREAK_SUGGESTION = (
    '您已经连续学习超过 2 小时，建议休息 10-15 分钟活动一下，'
    '有助于保持注意力和学习效率。'
)
SLEEP_SUGGESTION = (
    '已经晚上 10 点多了，建议您尽快准备休息。'
    '充足的睡眠对记忆巩固和第二天的学习状态至关重要。'
)


@shared_task(
    bind=True,
    time_limit=300,
    soft_time_limit=270,
    max_retries=3,
    default_retry_delay=60,
)
def generate_health_suggestions(self):
    """为所有活跃用户生成健康建议。

    规则:
    - 当前有进行中学习会话 (GoalSession) 且累计超过 120 分钟 → 'break' 建议
    - 当前时间超过 22:00 → 'sleep' 建议

    HUMAN-CENTRIC: 仅创建 DB 记录 (is_read=False)，不推送通知。
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    now = timezone.now()
    results = {'break': 0, 'sleep': 0, 'errors': 0}

    active_users = User.objects.filter(is_active=True)

    for user in active_users:
        try:
            if _generate_break_suggestion(user, now):
                results['break'] += 1
        except Exception as e:
            logger.error(
                'Break suggestion failed for user %d: %s', user.id, e
            )
            results['errors'] += 1

        try:
            if _generate_sleep_suggestion(user, now):
                results['sleep'] += 1
        except Exception as e:
            logger.error(
                'Sleep suggestion failed for user %d: %s', user.id, e
            )
            results['errors'] += 1

    logger.info(
        'Health suggestions generated — break: %d, sleep: %d (errors: %d)',
        results['break'], results['sleep'], results['errors'],
    )
    return {
        'break_suggestions': results['break'],
        'sleep_suggestions': results['sleep'],
        'errors': results['errors'],
    }


def _generate_break_suggestion(user, now):
    """检查是否需要生成 '休息' 建议。返回 True 表示已创建建议。"""
    from .models import HealthSuggestion

    try:
        from apps.goals.models import GoalSession
    except Exception:
        # GoalSession not yet implemented (ImportError)
        # or goals app not in INSTALLED_APPS (RuntimeError)
        return False

    # Check if user's total learning today exceeds 120 minutes
    today = now.date()
    total_minutes = (
        GoalSession.objects.filter(
            user=user,
            date=today,
        ).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
    )

    if total_minutes > 120:
        # Avoid duplicate suggestions within the same hour
        recent = HealthSuggestion.objects.filter(
            user=user,
            suggestion_type='break',
            created_at__gte=now - timedelta(hours=1),
        ).exists()
        if not recent:
            HealthSuggestion.objects.create(
                user=user,
                suggestion_type='break',
                content=BREAK_SUGGESTION,
                trigger_reason=(
                    f'连续学习 {total_minutes} 分钟'
                ),
            )
            return True

    return False


def _generate_sleep_suggestion(user, now):
    """检查是否需要生成 '睡眠' 建议（当前时间 > 22:00）。返回 True 表示已创建建议。"""
    from .models import HealthSuggestion

    if now.hour >= 22:
        # Only generate once per day
        today = now.date()
        already_generated = HealthSuggestion.objects.filter(
            user=user,
            suggestion_type='sleep',
            created_at__date=today,
        ).exists()
        if not already_generated:
            HealthSuggestion.objects.create(
                user=user,
                suggestion_type='sleep',
                content=SLEEP_SUGGESTION,
                trigger_reason='当前时间超过 22:00',
            )
            return True

    return False
