"""Surface Analytics — query and aggregate SurfaceEvent data for insights."""
import logging
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField

logger = logging.getLogger(__name__)


def get_surface_stats(user, days=30):
    """Get comprehensive surface engagement stats for a user.
    
    Returns dict with:
    - totals: total events, read, acted, dismissed
    - rates: read_rate, ctr (acted/read), dismiss_rate
    - by_type: per event_type breakdown
    - by_day: daily trend for last N days
    - avg_response_time: average time from created to acted
    """
    from infra.llm.models import SurfaceEvent
    
    since = timezone.now() - timezone.timedelta(days=days)
    qs = SurfaceEvent.objects.filter(user=user, created_at__gte=since)
    
    # Totals by status
    total = qs.count()
    read_count = qs.filter(status='read').count()
    acted_count = qs.filter(status='acted').count()
    dismissed_count = qs.filter(status='dismissed').count()
    pending_count = qs.filter(status='pending').count()
    
    # Rates
    non_pending = read_count + acted_count + dismissed_count
    read_rate = round(read_count / non_pending * 100, 1) if non_pending else 0
    ctr = round(acted_count / read_count * 100, 1) if read_count else 0
    dismiss_rate = round(dismissed_count / non_pending * 100, 1) if non_pending else 0
    
    # By event_type
    by_type = {}
    for et in dict(SurfaceEvent.TYPE_CHOICES):
        type_qs = qs.filter(event_type=et)
        t_total = type_qs.count()
        if t_total == 0:
            continue
        t_read = type_qs.filter(status='read').count()
        t_acted = type_qs.filter(status='acted').count()
        t_non_pending = t_read + t_acted + type_qs.filter(status='dismissed').count()
        by_type[et] = {
            'total': t_total,
            'read': t_read,
            'acted': t_acted,
            'ctr': round(t_acted / t_read * 100, 1) if t_read else 0,
        }
    
    # Daily trend (last 7 days)
    daily = []
    for i in range(6, -1, -1):
        day = timezone.localdate() - timezone.timedelta(days=i)
        day_qs = qs.filter(created_at__date=day)
        daily.append({
            'date': day.isoformat(),
            'total': day_qs.count(),
            'acted': day_qs.filter(status='acted').count(),
        })
    
    return {
        'period_days': days,
        'total': total,
        'read': read_count,
        'acted': acted_count,
        'dismissed': dismissed_count,
        'pending': pending_count,
        'read_rate': read_rate,
        'ctr': ctr,
        'dismiss_rate': dismiss_rate,
        'by_type': by_type,
        'daily_trend': daily,
    }


def get_summary(user):
    """Lightweight summary for dashboard/skill display."""
    stats = get_surface_stats(user, days=30)
    top_type = max(stats['by_type'].items(), key=lambda x: x[1]['acted']) if stats['by_type'] else ('N/A', {})
    return {
        'total_surfaces': stats['total'],
        'ctr': stats['ctr'],
        'read_rate': stats['read_rate'],
        'dismiss_rate': stats['dismiss_rate'],
        'most_effective_type': top_type[0],
        'most_effective_acted': top_type[1].get('acted', 0) if isinstance(top_type, tuple) and len(top_type) > 1 else 0,
    }
