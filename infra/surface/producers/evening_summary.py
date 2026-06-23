"""Evening Summary producer — generates a daily summary SurfaceEvent."""
import logging
from django.utils import timezone
from django.db.models import Sum
from infra.surface.service import create_event

logger = logging.getLogger(__name__)


def produce(user):
    """Generate evening summary for today's activity. Returns created count."""
    today = timezone.localdate()
    now = timezone.now()
    today_start = timezone.datetime.combine(today, timezone.datetime.min.time()).replace(tzinfo=now.tzinfo)
    created = 0
    
    # Today's learning minutes
    learning_minutes = 0
    try:
        from apps.goals.models import GoalSession
        result = GoalSession.objects.filter(user=user, date=today).aggregate(total=Sum('duration_minutes'))
        learning_minutes = result['total'] or 0
    except Exception:
        pass
    
    # Today's memories
    memories_today = 0
    try:
        from apps.memory.models import TrajectoryEvent
        memories_today = TrajectoryEvent.objects.filter(user=user, happened_at__gte=today_start).count()
    except Exception:
        pass
    
    # Today's conversations
    conversations_today = 0
    try:
        from apps.chat.models import Conversation
        conversations_today = Conversation.objects.filter(user=user, created_at__gte=today_start).count()
    except Exception:
        pass
    
    # Today's wellness
    wellness_today = False
    try:
        from apps.wellness.models import WellnessRecord
        wellness_today = WellnessRecord.objects.filter(user=user, record_date=today).exists()
    except Exception:
        pass
    
    # Active goals count
    active_goals = 0
    try:
        from apps.goals.models import Goal
        active_goals = Goal.objects.filter(user=user, status='active').count()
    except Exception:
        pass
    
    # Build summary text
    parts = []
    if learning_minutes:
        parts.append(f"今日学习 {learning_minutes} 分钟")
    else:
        parts.append("今日暂无学习记录")
    if memories_today:
        parts.append(f"新增 {memories_today} 条记忆")
    if conversations_today:
        parts.append(f"进行了 {conversations_today} 次对话")
    if wellness_today:
        parts.append("已记录身心健康")
    if active_goals:
        parts.append(f"{active_goals} 个活跃目标进行中")
    
    description = "；".join(parts)
    
    # Generate summary event (daily, dedup by date)
    event, is_new = create_event(
        user=user,
        event_type='summary',
        priority=5,
        title=f'{today.strftime("%m/%d")} 晚间总结',
        description=description,
        event_key=f'evening_summary:{today.isoformat()}',
        cta={'action': 'discuss', 'label': '查看详情', 'icon': 'moon-stars'},
    )
    
    if is_new:
        created = 1
        logger.info('Evening summary created for user %d: %s', user.pk, description[:60])
    else:
        logger.info('Evening summary updated for user %d', user.pk)
    
    return created
