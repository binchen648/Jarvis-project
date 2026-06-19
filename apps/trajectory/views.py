from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import SkillNode, UserLearningProgress, LearningPath, PathNode


@login_required
def skill_graph(request):
    """技能图谱 — 按分类分组的技能节点列表."""
    from itertools import groupby

    all_skills = SkillNode.objects.all().prefetch_related('prerequisites').order_by('category', 'difficulty', 'name')
    skills_by_category = {
        category: list(group)
        for category, group in groupby(all_skills, key=lambda s: s.category)
    }

    # Load user progress for current user and attach to each skill
    user_progress_map = {}
    if request.user.is_authenticated:
        progresses = UserLearningProgress.objects.filter(user=request.user).select_related('skill')
        for p in progresses:
            user_progress_map[p.skill_id] = p

    # Attach progress status directly to each skill for template convenience
    for skills in skills_by_category.values():
        for skill in skills:
            prog = user_progress_map.get(skill.id)
            if prog:
                skill.user_status = prog.status
                skill.user_status_display = prog.get_status_display()

    return render(request, 'trajectory/skill_graph.html', {
        'skills_by_category': skills_by_category,
    })


@login_required
def path_list(request):
    """用户的学习路径列表."""
    paths = LearningPath.objects.filter(user=request.user).prefetch_related('nodes')

    # Compute progress for each path
    path_progress = []
    for path in paths:
        nodes = list(path.nodes.all())
        total = len(nodes)
        completed = sum(1 for n in nodes if n.status == 'completed')
        path_progress.append({
            'path': path,
            'total': total,
            'completed': completed,
            'progress_pct': int(completed / total * 100) if total > 0 else 0,
        })

    return render(request, 'trajectory/path_list.html', {
        'path_progress': path_progress,
    })


@login_required
def path_detail(request, pk):
    """路径详情页 — 展示有序节点."""
    path = get_object_or_404(LearningPath, pk=pk, user=request.user)
    nodes = path.nodes.select_related('skill').order_by('order')

    # Compute overall progress
    total = nodes.count()
    completed = nodes.filter(status='completed').count()
    progress_pct = int(completed / total * 100) if total > 0 else 0

    return render(request, 'trajectory/path_detail.html', {
        'path': path,
        'nodes': nodes,
        'total': total,
        'completed': completed,
        'progress_pct': progress_pct,
    })


@login_required
@require_POST
def complete_node(request, pk):
    """用户手动确认节点完成（HUMAN-CENTRIC: 仅标记，不自动推进）. """
    node = get_object_or_404(PathNode, pk=pk, path__user=request.user)

    if node.status == 'completed':
        messages.info(request, f'节点「{node.skill.name if node.skill else "(已删除)"}」已经完成过了。')
        return JsonResponse({'status': 'already_completed'})

    node.status = 'completed'
    node.save(update_fields=['status'])

    # Also update user learning progress if linked
    if node.skill:
        progress, created = UserLearningProgress.objects.get_or_create(
            user=request.user,
            skill=node.skill,
            defaults={'status': 'completed'},
        )
        if not created and progress.status != 'completed':
            progress.status = 'completed'
            progress.save(update_fields=['status'])

    skill_name = node.skill.name if node.skill else '(已删除)'
    messages.success(request, f'🎉 恭喜完成「{skill_name}」！继续加油！')

    return JsonResponse({'status': 'ok', 'node_id': pk})
