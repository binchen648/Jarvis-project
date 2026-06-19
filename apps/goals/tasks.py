from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum

from .models import Goal, GoalSession

User = get_user_model()


@shared_task(
    time_limit=300,
    soft_time_limit=270,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def check_goal_deadlines():
    """检查即将到期的目标截止日期，发送温柔提醒（永不自动更改状态）。

    提醒规则：
    - 距 deadline <= 3 天且状态仍为 'active' 的目标会被标记提醒。
    - 不修改目标状态，仅生成提醒记录（通过 Event 或日志）。
    如果 eventbus.Event 尚未就绪，则仅输出日志。
    """
    from datetime import timedelta

    now = timezone.localdate()
    warning_window = now + timedelta(days=3)

    approaching = Goal.objects.filter(
        status='active',
        deadline__isnull=False,
        deadline__lte=warning_window,
        deadline__gte=now,
    ).select_related('user')

    count = 0
    for goal in approaching:
        days_left = (goal.deadline - now).days
        msg = (
            f'[目标提醒] 目标「{goal.title}」还剩 {days_left} 天 '
            f'（截止 {goal.deadline}），继续加油！'
        )
        # Try to emit via eventbus if available
        try:
            from infra.eventbus.models import Event
            Event.objects.create(
                user=goal.user,
                event_type='goal_deadline_warning',
                payload={
                    'title': '目标即将到期',
                    'description': msg,
                    'goal_id': goal.id,
                    'goal_title': goal.title,
                    'days_left': days_left,
                    'deadline': str(goal.deadline),
                },
            )
        except (ImportError, Exception):
            # Fallback: log only — the system will still work
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(msg)

        count += 1

    return f'Checked {count} approaching goals'


@shared_task(
    time_limit=600,
    soft_time_limit=540,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def aggregate_daily_sessions():
    """聚合每位用户每天的 GoalSession 总学习时长。

    输出：print/log 每个用户的每日学习汇总。
    将来可扩展为写入 TrajectoryEvent 或 Dashboard 统计表。
    """
    from datetime import timedelta

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    # Aggregate yesterday's sessions per user
    rows = list(
        GoalSession.objects
        .filter(date=yesterday)
        .values('user')
        .annotate(total_minutes=Sum('duration_minutes'))
        .order_by('user')
    )

    if not rows:
        return 'Aggregated 0 users'

    # Batch-fetch all users in one query instead of N individual queries
    user_ids = [r['user'] for r in rows]
    users = User.objects.in_bulk(user_ids)  # {pk: User, ...}

    results = []
    for row in rows:
        user = users.get(row['user'])
        if user:
            info = f'User {user.username}: {row["total_minutes"]} minutes on {yesterday}'
        else:
            info = f'User #{row["user"]}: {row["total_minutes"]} minutes on {yesterday}'
        results.append(info)

        # Emit to eventbus if available (uses user_id directly, no extra query)
        try:
            from infra.eventbus.models import Event
            Event.objects.create(
                user_id=row['user'],
                event_type='daily_session_aggregate',
                payload={
                    'title': '学习时长汇总',
                    'description': info,
                    'date': str(yesterday),
                    'total_minutes': row['total_minutes'],
                },
            )
        except (ImportError, Exception):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(info)

    return f'Aggregated {len(results)} users'
