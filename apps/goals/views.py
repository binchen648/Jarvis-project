from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, Prefetch

from .models import Goal, GoalProgress, GoalSession


# ── Forms ──────────────────────────────────────────────────────────────────


class GoalForm(forms.ModelForm):
    """目标表单."""

    class Meta:
        model = Goal
        fields = [
            'title', 'description', 'goal_type', 'target_value', 'target_unit',
            'category', 'is_recurring', 'deadline', 'status',
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class GoalSessionForm(forms.ModelForm):
    """学习记录表单."""

    class Meta:
        model = GoalSession
        fields = ['goal', 'duration_minutes', 'note', 'content_ref']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['goal'].queryset = Goal.objects.filter(
                user=self.user, status='active'
            )
            self.fields['goal'].required = False
            self.fields['goal'].empty_label = '无关联目标（自由记录）'


# ── Views ──────────────────────────────────────────────────────────────────


@login_required
def goal_list(request):
    """目标列表页."""
    goals = Goal.objects.filter(user=request.user).prefetch_related(
        Prefetch('progress_records',
                 queryset=GoalProgress.objects.order_by('-recorded_at'),
                 to_attr='_latest_progresses')
    )
    status_filter = request.GET.get('status', '')
    if status_filter in dict(Goal.STATUS_CHOICES):
        goals = goals.filter(status=status_filter)

    # Single aggregate query: total minutes per goal for this user
    session_totals = dict(
        GoalSession.objects.filter(user=request.user)
        .exclude(goal__isnull=True)
        .values('goal_id')
        .annotate(total=Sum('duration_minutes'))
        .values_list('goal_id', 'total')
    )

    # Build goal_data — NO per-goal queries (prefetched + aggregated)
    goal_data = []
    for goal in goals:
        progresses = getattr(goal, '_latest_progresses', [])
        latest_progress = progresses[0] if progresses else None
        total_minutes = session_totals.get(goal.pk, 0)
        goal_data.append({
            'goal': goal,
            'latest_progress': latest_progress,
            'total_minutes': total_minutes,
        })

    return render(request, 'goals/goal_list.html', {
        'goal_data': goal_data,
        'active_count': Goal.objects.filter(user=request.user, status='active').count(),
        'current_status': status_filter,
    })


@login_required
def goal_create(request):
    """创建目标."""
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, '目标创建成功！')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        initial = {}
        if request.GET.get('title'):
            initial['title'] = request.GET['title'][:300]
        if request.GET.get('description'):
            initial['description'] = request.GET['description'][:2000]
        form = GoalForm(initial=initial)

    return render(request, 'goals/goal_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def goal_detail(request, pk):
    """目标详情页."""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    sessions = GoalSession.objects.filter(goal=goal, user=request.user)[:20]
    progress_records = goal.progress_records.all()[:10]
    total_minutes = GoalSession.objects.filter(
        goal=goal, user=request.user
    ).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0

    return render(request, 'goals/goal_detail.html', {
        'goal': goal,
        'sessions': sessions,
        'progress_records': progress_records,
        'total_minutes': total_minutes,
    })


@login_required
def goal_edit(request, pk):
    """编辑目标."""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, '目标已更新！')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = GoalForm(instance=goal)

    return render(request, 'goals/goal_form.html', {
        'form': form,
        'is_create': False,
        'goal': goal,
    })


@login_required
@require_POST
def update_status(request, pk):
    """更新目标状态 — HTMX 端点，需用户手动确认."""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    # Cycle: active → completed → abandoned → active (manual confirmation)
    status_cycle = {'active': 'completed', 'completed': 'abandoned', 'abandoned': 'active'}
    goal.status = status_cycle.get(goal.status, 'active')
    goal.save()

    messages.success(request, f'目标「{goal.title}」状态已更新为：{goal.get_status_display()}')

    # HTMX: return a small fragment to swap the status badge
    return render(request, 'goals/_status_badge.html', {'goal': goal})


@login_required
def log_session(request):
    """记录学习时段."""
    if request.method == 'POST':
        form = GoalSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            messages.success(request, '学习记录已保存！')
            return redirect('goals:goal_list')
    else:
        form = GoalSessionForm(user=request.user)

    return render(request, 'goals/goal_session_form.html', {
        'form': form,
    })
