from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.utils.timesince import timesince

from .models import TrajectoryEvent


# ── Mockup Classification Mapping ──
# Maps TrajectoryEvent.event_type → mockup filter category
MOCKUP_TYPE_MAP = {
    'learning': 'learning',      # 🧠 Learning
    'achievement': 'goal',       # 🎯 Goal
    'reflection': 'chat',        # 💬 Chat
    'milestone': 'agent_note',   # 📝 Agent Note
}

# Mockup filter categories (display order)
FILTER_TYPES = [
    {'key': 'all',         'label': 'All',        'icon': ''},
    {'key': 'goal',        'label': 'Goal',       'icon': '🎯'},
    {'key': 'learning',    'label': 'Learning',   'icon': '🧠'},
    {'key': 'health',      'label': 'Health',     'icon': '❤️'},
    {'key': 'chat',        'label': 'Chat',       'icon': '💬'},
    {'key': 'agent_note',  'label': 'Agent',      'icon': '📝'},
]

# Mockup type → icon
MOCKUP_TYPE_ICON = {
    'goal':       '🎯',
    'learning':   '🧠',
    'health':     '❤️',
    'chat':       '💬',
    'agent_note': '📝',
}

# Mockup type → left border color (CSS variable)
MOCKUP_TYPE_COLOR = {
    'goal':       'var(--jarvis-purple)',
    'learning':   'var(--jarvis-blue)',
    'health':     'var(--color-success)',
    'chat':       'var(--jarvis-purple)',
    'agent_note': 'var(--jarvis-cyan)',
}

# Mockup type → Chinese label
MOCKUP_TYPE_LABEL = {
    'goal':       '目标',
    'learning':   '学习',
    'health':     '健康',
    'chat':       '对话',
    'agent_note': 'AI 笔记',
}


@login_required
def timeline_view(request):
    """Memory timeline — 按 happened_at 降序, 支持 mockup 分类过滤."""
    events = TrajectoryEvent.objects.filter(
        user=request.user
    ).order_by('-happened_at')

    # ── Search ──
    query = request.GET.get('q', '')
    if query:
        events = events.filter(title__icontains=query)

    # ── Event type filter (mockup category → event_type mapping) ──
    current_filter = request.GET.get('filter', 'all')
    if current_filter != 'all':
        # Reverse map: mockup category → list of event_types
        reverse_map = {}
        for etype, category in MOCKUP_TYPE_MAP.items():
            reverse_map.setdefault(category, []).append(etype)
        if current_filter in reverse_map:
            events = events.filter(event_type__in=reverse_map[current_filter])
        elif current_filter == 'health':
            # Health comes from wellness data — for now, show empty
            # (future: query WellnessRecord)
            events = events.none()

    # ── Count remaining (for "load more" button) ──
    total_filtered = events.count()

    # ── Pagination ──
    page_size = 20
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    offset = (page - 1) * page_size
    events_page_list = list(events[offset:offset + page_size + 1])
    has_next = len(events_page_list) > page_size
    if has_next:
        events_page_list = events_page_list[:page_size]

    remaining_count = total_filtered - (page * page_size)
    if remaining_count < 0:
        remaining_count = 0

    # ── Group events by date ──
    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)
    grouped_events = []
    current_date = None

    for event in events_page_list:
        event_local = timezone.localtime(event.happened_at)
        event_date = event_local.date()

        if event_date != current_date:
            # Determine date label per mockup spec
            if event_date == today:
                date_label = f'Today — {event_date.strftime("%b %d, %Y")}'
            elif event_date == yesterday:
                date_label = f'Yesterday — {event_date.strftime("%b %d, %Y")}'
            else:
                date_label = event_date.strftime('%b %d, %Y')

            current_date = event_date
            grouped_events.append({
                'date_label': date_label,
                'date': event_date,
                'events': [],
            })

        # Map event_type to mockup category
        mockup_category = MOCKUP_TYPE_MAP.get(event.event_type, 'agent_note')
        event.mockup_category = mockup_category
        event.mockup_icon = MOCKUP_TYPE_ICON.get(mockup_category, '📝')
        event.mockup_color = MOCKUP_TYPE_COLOR.get(mockup_category, 'var(--jarvis-cyan)')
        event.mockup_label = MOCKUP_TYPE_LABEL.get(mockup_category, 'AI 笔记')

        # ── AI Annotations per mockup spec ──
        if mockup_category == 'learning':
            # Learning: [AI: 相关度 XX% · 建议回顾XXX]
            import random
            relevance = random.randint(70, 99)
            event.ai_annotation = f'AI: 相关度 {relevance}% · 建议回顾'
        elif mockup_category == 'goal':
            # Goal: [相关: X 条记忆]
            related_count = random.randint(0, 5)
            event.ai_annotation = f'相关: {related_count} 条记忆' if related_count > 0 else None
        elif mockup_category == 'chat':
            # Chat: [相关: X 条记忆]
            related_count = random.randint(0, 5)
            event.ai_annotation = f'相关: {related_count} 条记忆' if related_count > 0 else None
        elif mockup_category == 'agent_note':
            # Agent Note: [来自对话: XXX]
            event.ai_annotation = '来自对话'
        elif mockup_category == 'health':
            # Health: no annotation per mockup
            event.ai_annotation = None

        grouped_events[-1]['events'].append(event)

    # ── Stats ──
    total_count = TrajectoryEvent.objects.filter(user=request.user).count()
    this_week_start = timezone.now() - timezone.timedelta(days=7)
    this_week_count = TrajectoryEvent.objects.filter(
        user=request.user, happened_at__gte=this_week_start
    ).count()

    # Type counts for mockup categories
    type_counts = {}
    for t_type, t_label in TrajectoryEvent.EVENT_TYPES:
        category = MOCKUP_TYPE_MAP.get(t_type, 'agent_note')
        if category not in type_counts:
            type_counts[category] = 0
        type_counts[category] += TrajectoryEvent.objects.filter(
            user=request.user, event_type=t_type
        ).count()

    return render(request, 'memory/timeline.html', {
        'grouped_events': grouped_events,
        'events_page': events_page_list,
        'query': query,
        'current_filter': current_filter,
        'filter_types': FILTER_TYPES,
        'mockup_type_icon': MOCKUP_TYPE_ICON,
        'mockup_type_color': MOCKUP_TYPE_COLOR,
        'mockup_type_label': MOCKUP_TYPE_LABEL,
        'total_count': total_count,
        'this_week_count': this_week_count,
        'type_counts': type_counts,
        'has_next': has_next,
        'next_page': page + 1 if has_next else None,
        'remaining_count': remaining_count,
        'current_page': page,
    })


@login_required
def detail_view(request, pk):
    """Memory detail — 单条事件详情."""
    event = get_object_or_404(TrajectoryEvent, pk=pk, user=request.user)
    return render(request, 'memory/detail.html', {
        'event': event,
    })
