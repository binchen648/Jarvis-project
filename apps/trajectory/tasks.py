import logging
from celery import shared_task
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    time_limit=300,
    soft_time_limit=270,
    max_retries=3,
    default_retry_delay=60,
)
def update_skill_stats(self):
    """每日更新技能节点统计：重新计算 learner_count 和 avg_completion_rate.

    优化说明：原实现每次循环对每个 SkillNode 执行 3 次独立查询，
    改写为一次聚合查询拿到全部统计后批量更新。
    """
    from .models import SkillNode, UserLearningProgress

    # Single aggregate query: get all stats per skill at once
    stats = dict(
        UserLearningProgress.objects.values('skill_id').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            unique_users=Count('user', distinct=True),
        ).values_list('skill_id', 'unique_users', 'total', 'completed')
    )
    # stats = {skill_id: (unique_users, total, completed), ...}

    skill_list = list(SkillNode.objects.all())
    total = len(skill_list)
    updated_count = 0

    for skill in skill_list:
        try:
            row = stats.get(skill.pk)
            if row:
                unique_users, total, completed = row
                completion_rate = completed / total if total > 0 else None
            else:
                unique_users = 0
                completion_rate = None

            SkillNode.objects.filter(pk=skill.pk).update(
                learner_count=unique_users,
                avg_completion_rate=completion_rate,
            )
            updated_count += 1

        except Exception as e:
            logger.error("Failed to update stats for SkillNode %d (%s): %s", skill.pk, skill.name, e)

    logger.info("Updated stats for %d/%d skill nodes", updated_count, total)
    return {'updated': updated_count, 'total': total}


@shared_task(
    bind=True,
    time_limit=600,
    soft_time_limit=540,
    max_retries=3,
    default_retry_delay=60,
)
def check_path_progress(self):
    """每日检查路径进度，对接近完成或停滞的路径生成温和提示（human-centric: 不自动推进）. """
    from .models import LearningPath, PathNode

    now_approx_complete = 0
    stuck_paths = 0

    paths = LearningPath.objects.filter(is_active=True).prefetch_related('nodes')

    for path in paths:
        try:
            nodes = list(path.nodes.all())
            if not nodes:
                continue

            total = len(nodes)
            completed = sum(1 for n in nodes if n.status == 'completed')
            in_progress = sum(1 for n in nodes if n.status == 'in_progress')

            # Detecting "almost complete" paths
            if completed > 0 and completed == total - 1:
                # One node left — gentle nudge
                next_node = next((n for n in nodes if n.status != 'completed'), None)
                if next_node and next_node.skill:
                    logger.info(
                        "PATH ALMOST DONE — path=%s (pk=%d): %d/%d completed. "
                        "Last node: %s. Consider gently reminding the user.",
                        path.title, path.pk, completed, total,
                        next_node.skill.name,
                    )
                    now_approx_complete += 1

            # Detecting "stuck" paths
            if completed == 0 and in_progress == 0 and total > 0:
                # Path never started
                logger.info(
                    "PATH NOT STARTED — path=%s (pk=%d): %d nodes waiting.",
                    path.title, path.pk, total,
                )
                stuck_paths += 1

        except Exception as e:
            logger.error("Failed to check path %d: %s", path.pk, e)

    logger.info(
        "Path check complete: %d almost done, %d not started (out of %d active paths).",
        now_approx_complete, stuck_paths, len(paths),
    )
    return {
        'paths_checked': len(paths),
        'almost_complete': now_approx_complete,
        'not_started': stuck_paths,
    }
