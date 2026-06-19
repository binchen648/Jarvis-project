from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib import messages

from .models import HealthSuggestion, WellnessRecord


@login_required
def suggestion_list(request):
    """列出当前用户未读的健康建议 (HTMX 就绪)."""
    suggestions = HealthSuggestion.objects.filter(
        user=request.user, is_read=False
    )
    return render(request, 'wellness/suggestion_list.html', {
        'suggestions': suggestions,
    })


@login_required
@require_POST
def dismiss_suggestion(request, pk):
    """标记健康建议为已读 (HTMX 内联删除卡片)."""
    suggestion = get_object_or_404(
        HealthSuggestion, pk=pk, user=request.user
    )
    suggestion.is_read = True
    suggestion.save(update_fields=['is_read'])
    return HttpResponse('')


@login_required
def record_create(request):
    """创建身心健康记录."""
    if request.method == 'POST':
        try:
            mood_score = int(request.POST.get('mood_score', 0))
        except (ValueError, TypeError):
            mood_score = 0
        if mood_score not in range(1, 6):  # 1-5 only
            messages.error(request, '心情评分必须在 1-5 之间。')
            return render(request, 'wellness/record_form.html')

        sleep_raw = request.POST.get('sleep_hours', '')
        sleep_hours = float(sleep_raw) if sleep_raw else None
        exercise_raw = request.POST.get('exercise_minutes', '')
        exercise_minutes = int(exercise_raw) if exercise_raw else None
        note = request.POST.get('note', '')

        record = WellnessRecord.objects.create(
            user=request.user,
            mood_score=mood_score,
            sleep_hours=sleep_hours,
            exercise_minutes=exercise_minutes,
            note=note,
        )
        messages.success(request, '身心健康记录已保存！')
        return redirect('wellness:record_create')

    return render(request, 'wellness/record_form.html')
