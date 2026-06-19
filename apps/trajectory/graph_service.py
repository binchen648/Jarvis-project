"""Knowledge Graph query service for persona/memory retrieval."""

from .models import UserInterest, UserLearningProgress


def get_user_interests(user, min_weight=0.5):
    """获取用户兴趣标签（权重高于阈值）."""
    return list(UserInterest.objects.filter(user=user, weight__gte=min_weight))


def get_related_skills(user, tags=None):
    """根据用户兴趣或标签获取相关技能节点."""
    from .models import SkillNode
    if tags:
        return SkillNode.objects.filter(category__in=tags)[:10]
    interests = get_user_interests(user)
    categories = [i.tag for i in interests]
    return SkillNode.objects.filter(category__in=categories)[:10]


def get_user_skill_graph(user):
    """获取用户学习进度映射到技能节点."""
    return UserLearningProgress.objects.filter(user=user).select_related('skill')


def get_recommended_content_by_interest(user, limit=5):
    """根据用户兴趣标签获取推荐内容."""
    from apps.content.models import ProcessedContent
    interests = get_user_interests(user)
    if not interests:
        return ProcessedContent.objects.none()
    content = ProcessedContent.objects.filter(
        stage='active', tags__overlap=[i.tag for i in interests]
    )[:limit]
    return content
