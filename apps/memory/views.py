import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timesince import timesince

from .models import TrajectoryEvent
from django.views.decorators.http import require_POST


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
@require_POST
def send_to_agent(request, pk):
    """Memory → Agent: 发送记忆到 Agent 对话."""
    event = get_object_or_404(TrajectoryEvent, pk=pk, user=request.user)
    from apps.chat.models import Conversation, Message
    conv = Conversation.objects.create(
        user=request.user,
        title=f"记忆: {event.title[:40]}"
    )
    type_label = dict(TrajectoryEvent.EVENT_TYPES).get(event.event_type, event.event_type)
    Message.objects.create(
        conversation=conv, role='user',
        content=f"关于这条记忆:\n\n{event.title}\n{event.description or ''}\n\n类型: {type_label}\n时间: {event.happened_at.strftime('%Y-%m-%d %H:%M')}\n\n请帮我分析这条记忆并给出建议。"
    )
    return redirect('chat:conversation_detail', pk=conv.pk)


@login_required
def log_from_goal(request):
    """Goal → Memory: 目标完成写入记忆 (POST from goal form)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    event_type = data.get('event_type', 'achievement')
    valid_types = dict(TrajectoryEvent.EVENT_TYPES).keys()
    if event_type not in valid_types:
        return JsonResponse({'error': f'invalid event_type, must be one of {",".join(valid_types)}'}, status=400)
    if not title:
        return JsonResponse({'error': 'title required'}, status=400)
    event = TrajectoryEvent.objects.create(
        user=request.user,
        event_type=event_type,
        title=title[:300],
        description=description[:2000],
        happened_at=timezone.now(),
    )
    return JsonResponse({'ok': True, 'pk': event.pk})


@login_required
def detail_view(request, pk):
    """Memory detail — 单条事件详情."""
    event = get_object_or_404(TrajectoryEvent, pk=pk, user=request.user)
    return render(request, 'memory/detail.html', {
        'event': event,
    })


@login_required
def graph_data(request):
    """返回认知图谱 JSON 数据 (nodes + edges) 给 Cytoscape.js."""
    nodes = []
    edges = []
    node_ids = set()
    edge_keys = set()
    rank = 0

    # ── 1) SkillNode → 知识图谱骨架 ──
    try:
        from apps.trajectory.models import SkillNode, UserLearningProgress
        skills = SkillNode.objects.all().select_related()
        skill_map = {}
        for s in skills:
            nid = f"skill_{s.id}"
            skill_map[s.id] = nid
            if nid not in node_ids:
                # Determine node color by difficulty
                diff_colors = {1: '#22C55E', 2: '#06B6D4', 3: '#8B5CF6', 4: '#F59E0B', 5: '#EF4444'}
                color = diff_colors.get(s.difficulty, '#8B5CF6')
                node_ids.add(nid)
                nodes.append({
                    'data': {
                        'id': nid, 'label': s.name,
                        'type': 'skill', 'difficulty': s.difficulty,
                        'category': s.category, 'color': color,
                        'estimated_hours': s.estimated_hours,
                    },
                    'position': {'x': rank * 80 % 1200, 'y': rank * 60 % 600},
                })
                rank += 1

        # Skill prerequisite edges
        for s in skills:
            nid = skill_map[s.id]
            for prereq in s.prerequisites.all():
                pid = skill_map.get(prereq.id)
                if pid:
                    ekey = f"{pid}->{nid}"
                    if ekey not in edge_keys:
                        edge_keys.add(ekey)
                        edges.append({
                            'data': {
                                'id': ekey, 'source': pid, 'target': nid,
                                'label': 'prerequisite', 'color': '#555',
                            }
                        })

        # User learning progress → color enhancement
        try:
            progress_qs = UserLearningProgress.objects.filter(user=request.user)
            for p in progress_qs:
                nid = skill_map.get(p.skill_id)
                if nid:
                    status_colors = {'not_started': '#444', 'learning': '#8B5CF6', 'completed': '#22C55E', 'struggling': '#EF4444'}
                    for n in nodes:
                        if n['data']['id'] == nid:
                            n['data']['status'] = p.status
                            n['data']['color'] = status_colors.get(p.status, n['data']['color'])
                            n['data']['predicted_days'] = p.predicted_completion_days
        except Exception:
            logger.exception("graph_data user_learning_progress failed")
    except Exception:
        logger.exception("graph_data skills section failed")

    # ── 2) UserInterest → 兴趣节点 ──
    try:
        from apps.trajectory.models import UserInterest
        interests = UserInterest.objects.filter(user=request.user, weight__gte=0.5)[:30]
        for interest in interests:
            nid = f"interest_{interest.id}"
            if nid not in node_ids:
                node_ids.add(nid)
                nodes.append({
                    'data': {
                        'id': nid, 'label': interest.tag,
                        'type': 'interest', 'weight': interest.weight,
                        'source': interest.source, 'color': '#F59E0B',
                    },
                    'position': {'x': rank * 100 % 1200, 'y': rank * 70 % 600},
                })
                rank += 1

            # Edge: interest → matching skills (by category name overlap)
            for s in skills:
                if interest.tag.lower() in s.name.lower() or s.category.lower() in interest.tag.lower():
                    ekey = f"{nid}->skill_{s.id}"
                    if ekey not in edge_keys:
                        edge_keys.add(ekey)
                        edges.append({
                            'data': {
                                'id': ekey, 'source': nid, 'target': f"skill_{s.id}",
                                'label': 'related', 'color': '#F59E0B',
                            }
                        })
    except Exception:
        logger.exception("graph_data interests section failed")

    # ── 3) TrajectoryEvent → 近期记忆节点 ──
    try:
        recent_events = TrajectoryEvent.objects.filter(
            user=request.user
        ).order_by('-happened_at')[:20]
        event_type_colors = {
            'learning': '#22C55E', 'achievement': '#8B5CF6',
            'reflection': '#06B6D4', 'milestone': '#F59E0B',
        }
        for ev in recent_events:
            nid = f"event_{ev.id}"
            if nid not in node_ids:
                node_ids.add(nid)
                color = event_type_colors.get(ev.event_type, '#686880')
                nodes.append({
                    'data': {
                        'id': nid, 'label': ev.title[:40],
                        'type': 'event', 'event_type': ev.event_type,
                        'color': color, 'timestamp': ev.happened_at.isoformat(),
                        'pk': ev.pk,
                    },
                    'position': {'x': rank * 80 + 200, 'y': rank * 50 % 600},
                })
                rank += 1

            # Connect event to related skills/interests by keyword overlap
            for n in nodes:
                target_id = n['data']['id']
                if target_id == nid:
                    continue
                label_lower = n['data'].get('label', '').lower()
                if any(word in label_lower for word in ev.title.lower().split()[:3]):
                    ekey = f"{nid}->{target_id}"
                    if ekey not in edge_keys:
                        edge_keys.add(ekey)
                        edges.append({
                            'data': {
                                'id': ekey, 'source': nid, 'target': target_id,
                                'label': 'related', 'color': '#444',
                            }
                        })
    except Exception:
        logger.exception("graph_data events section failed")

    return JsonResponse({'nodes': nodes, 'edges': edges})
