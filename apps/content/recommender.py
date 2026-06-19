"""推荐引擎 — 4路召回 + 3级排序 + 冷启动策略"""
import logging
import random
from typing import List, Optional
from django.db import models

logger = logging.getLogger(__name__)


# === Cold Start Stage Detection ===

def get_user_stage(user) -> int:
    """判断用户冷启动阶段。
    Stage 0: 刚注册, 无 Creator 订阅
    Stage 1: 有订阅无行为
    Stage 2: 少量行为
    Stage 3: 成熟用户
    """
    from .models import Creator
    
    subscription_count = Creator.objects.filter(
        contents__isnull=False
    ).distinct().count()
    # Check if user has any goals (behavior signal)
    session_count = 0
    try:
        from apps.goals.models import GoalSession
        session_count = GoalSession.objects.filter(user=user).count()
    except (ImportError, Exception):
        pass

    if subscription_count == 0:
        return 0
    elif session_count == 0:
        return 1
    elif session_count < 10:
        return 2
    else:
        return 3


# === 4-Recall Methods ===

def subscription_recall(user, limit=50) -> List[int]:
    """Subscription Recall — 用户订阅的 Creator 最新内容。
    
    当前为简化实现：返回所有活跃内容。
    TODO: Phase 4/5 接入 FavoriteCreator 模型后，按用户实际订阅过滤。
    """
    from .models import ProcessedContent

    content_ids = list(
        ProcessedContent.objects.filter(
            stage='active',
            creator__isnull=False,
        )
        .order_by('-published_at')
        .values_list('id', flat=True)[:limit]
    )
    logger.debug("Subscription recall: %d items (TODO: filter by user)", len(content_ids))
    return content_ids


def similar_recall(user, limit=50) -> List[int]:
    """Similar Recall — 基于向量相似度召回。
    当前使用简化实现：返回同标签内容。
    TODO: 接入 PgVector ANN 搜索 (pgvector ivfflat index)
    """
    from .models import ProcessedContent

    # 简化版：返回高质量活跃内容
    content_ids = list(
        ProcessedContent.objects.filter(
            stage='active',
            quality_score__gte=3.0,
        )
        .order_by('-quality_score', '-published_at')
        .values_list('id', flat=True)[:limit]
    )
    logger.debug("Similar recall: %d items", len(content_ids))
    return content_ids


def trending_recall(user, limit=30) -> List[int]:
    """Trending Recall — 平台热门内容"""
    from .models import ProcessedContent

    content_ids = list(
        ProcessedContent.objects.filter(
            stage='active',
            quality_score__gte=4.0,
        )
        .order_by('-quality_score')[:limit]
        .values_list('id', flat=True)
    )
    logger.debug("Trending recall: %d items", len(content_ids))
    return content_ids


def explore_recall(user, limit=20) -> List[int]:
    """Explore Recall — 探索新领域 (占总推荐 5%-15%)
    
    使用 ID 范围随机采样代替 ORDER BY RANDOM() 以避免全表扫描。
    """
    from .models import ProcessedContent

    # Get ID range for random sampling
    id_range = ProcessedContent.objects.filter(
        stage='active',
    ).aggregate(
        min_id=models.Min('id'),
        max_id=models.Max('id'),
    )

    min_id = id_range['min_id']
    max_id = id_range['max_id']

    if min_id is None or max_id is None:
        return []

    # Sample random IDs and fetch matching active content
    random_ids = [random.randint(min_id, max_id) for _ in range(limit * 3)]
    content_ids = list(
        ProcessedContent.objects.filter(
            id__in=random_ids, stage='active',
        ).values_list('id', flat=True)[:limit]
    )

    logger.debug("Explore recall: %d items (ID random sample)", len(content_ids))
    return content_ids


# === Multi-Recall Merger ===

def multi_recall(user, stage: int) -> List[int]:
    """多路召回合并，按冷启动阶段调整各路权重"""
    all_ids = []

    if stage == 0:
        # Stage 0: 热门为主 + 探索
        all_ids = trending_recall(user, 30) + explore_recall(user, 20)
    elif stage == 1:
        # Stage 1: 订阅为主 + 热门补充
        all_ids = subscription_recall(user, 40) + trending_recall(user, 20)
    elif stage == 2:
        # Stage 2: 订阅 + 相似 + 热门
        all_ids = (subscription_recall(user, 30) +
                   similar_recall(user, 20) +
                   trending_recall(user, 15))
    else:
        # Stage 3: 完整 4 路
        all_ids = (subscription_recall(user, 30) +
                   similar_recall(user, 20) +
                   trending_recall(user, 15) +
                   explore_recall(user, 10))

    # 去重并保持顺序
    seen = set()
    unique = []
    for cid in all_ids:
        if cid not in seen:
            seen.add(cid)
            unique.append(cid)

    return unique


# === 3-Tier Ranking ===

def coarse_rank(content_ids: List[int], limit=100) -> List[int]:
    """粗排: 规则过滤 — quality > 3, 排除低质量内容"""
    from .models import ProcessedContent

    candidates = ProcessedContent.objects.filter(
        id__in=content_ids,
        quality_score__gte=3.0,
    ).order_by('-quality_score')[:limit]

    return [c.id for c in candidates]


def fine_rank(user, content_ids: List[int], limit=50) -> List[int]:
    """精排: 加权评分排序。
    评分公式: 0.4×quality + 0.3×recency + 0.2×match + 0.1×random
    TODO: 接入 LGBM 模型进行精排
    """
    from .models import ProcessedContent
    from django.utils import timezone
    import random

    contents = ProcessedContent.objects.filter(id__in=content_ids)

    scored = []
    now = timezone.now()
    for c in contents:
        # quality score (0-5 normalized to 0-1)
        q_score = min(c.quality_score / 5.0, 1.0)

        # recency score (days since published, 0-30 days mapped to 1-0)
        if c.published_at is not None:
            days_since = (now - c.published_at).days
            r_score = max(1.0 - days_since / 30.0, 0.0)
        else:
            r_score = 0.0

        # match score (placeholder)
        m_score = 0.5

        # small random factor for diversity
        rand = random.random() * 0.1

        total = 0.4 * q_score + 0.3 * r_score + 0.2 * m_score + rand
        scored.append((total, c.id))

    scored.sort(key=lambda x: -x[0])
    return [cid for _, cid in scored[:limit]]


def llm_rerank(user, content_ids: List[int], limit=15) -> List[int]:
    """LLM 重排。
    当前为占位实现，直接返回精排结果。
    TODO: Phase 4 对接 LLM 进行多样性 + 惊喜感重排
    """
    return content_ids[:limit]


# === Main Entry Point ===

def get_recommendations_for_user(user, limit=20) -> List[int]:
    """为用户生成推荐列表的主入口"""
    logger.info("Generating recommendations for user %d", user.id)

    # 1. Detect cold start stage
    stage = get_user_stage(user)
    logger.debug("User %d at stage %d", user.id, stage)

    # 2. Multi-recall
    recalled = multi_recall(user, stage)
    if not recalled:
        logger.warning("No recall results for user %d", user.id)
        return []

    # 3. Coarse ranking
    coarse = coarse_rank(recalled, limit=100)
    if not coarse:
        return []

    # 4. Fine ranking
    fine = fine_rank(user, coarse, limit=50)
    if not fine:
        return []

    # 5. LLM rerank (placeholder)
    final = llm_rerank(user, fine, limit=limit)

    # 6. Fallback: if pipeline returns empty, try trending recall
    if not final:
        logger.info("Pipeline empty for user %d, falling back to trending", user.id)
        trending_ids = trending_recall(user, limit=limit)
        final = llm_rerank(user, trending_ids, limit=limit)

    logger.info("User %d: %d/%d/%d/%d recommendations (recall/coarse/fine/final)",
                 user.id, len(recalled), len(coarse), len(fine), len(final))
    return final
