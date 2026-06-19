"""Memory Service — 多级记忆服务 (Hermes-inspired L1/L2/L3).

提供 L1 核心画像、L2 上下文、L3 细节检索以及记忆的存储、
搜索、过期管理和统计功能。

Usage:
    profile = get_level1_profile(user)
    context = get_level2_context(user)
    results = search_memories(user, "python", level=3, memory_type='insight')
    entry = store_memory(user, level=2, memory_type='conversation', content='...')
    count = deactivate_expired()
    stats = get_memory_stats(user)
"""

import logging
from datetime import datetime
from typing import Optional

from django.db import models, transaction
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_level1_profile(user) -> dict:
    """获取用户的 L1 核心画像。

    从 MemoryEntry (level=1, is_active=True) 中查询，按 weight 降序排列。
    如果没有任何 L1 记录，尝试从 UserPersona 读取 fallback 数据。

    Args:
        user: User 模型实例。

    Returns:
        dict: {
            'summary': str,          # 画像摘要
            'facts': list[str],      # 用户事实列表
            'interests': list[dict], # 兴趣标签列表
            'version': int,          # 画像版本号
        }
    """
    from infra.llm.models import MemoryEntry

    try:
        entries = MemoryEntry.objects.filter(
            user=user, level=1, is_active=True
        ).order_by('-weight')

        result = {
            'summary': '',
            'facts': [],
            'interests': [],
            'version': 0,
        }

        for entry in entries:
            if entry.memory_type == 'persona_summary' and not result['summary']:
                result['summary'] = entry.content
            elif entry.memory_type == 'user_fact':
                result['facts'].append(entry.content)
            elif entry.memory_type == 'interest':
                result['interests'].append({
                    'tag': entry.content,
                    'weight': entry.weight,
                })

        if result['summary'] or result['facts'] or result['interests']:
            return result

    except Exception as e:
        logger.warning("Error querying L1 MemoryEntry for user %s: %s", user, e)

    # Fallback: 从 UserPersona 读取
    return _fallback_level1(user)


def _fallback_level1(user) -> dict:
    """从 UserPersona 获取 fallback L1 画像数据。"""
    from infra.llm.models import UserPersona

    try:
        persona = UserPersona.objects.get(user=user)
        return {
            'summary': persona.persona_summary or '',
            'facts': list(persona.facts or []),
            'interests': list(persona.interests or []),
            'version': persona.version,
        }
    except UserPersona.DoesNotExist:
        return {'summary': '', 'facts': [], 'interests': [], 'version': 0}
    except Exception as e:
        logger.warning("Error reading UserPersona fallback for user %s: %s", user, e)
        return {'summary': '', 'facts': [], 'interests': [], 'version': 0}


def get_level2_context(user) -> dict:
    """获取用户的 L2 上下文。

    查询 MemoryEntry (level=2, is_active=True)，按 weight 降序排列，
    按 memory_type 分组整理为结构化上下文。

    Args:
        user: User 模型实例。

    Returns:
        dict: {
            'goals': list[str],         # 学习目标列表
            'skills': list[str],        # 技能进度列表
            'wellness': str,            # 身心健康摘要
            'today_summary': str,       # 今日学习摘要
        }
    """
    from infra.llm.models import MemoryEntry

    result = {
        'goals': [],
        'skills': [],
        'wellness': '',
        'today_summary': '',
    }

    try:
        entries = MemoryEntry.objects.filter(
            user=user, level=2, is_active=True
        ).order_by('-weight')

        for entry in entries:
            if entry.memory_type == 'goal':
                result['goals'].append(entry.content)
            elif entry.memory_type == 'skill_progress':
                result['skills'].append(entry.content)
            elif entry.memory_type == 'wellness' and not result['wellness']:
                result['wellness'] = entry.content
            elif entry.memory_type == 'conversation' and not result['today_summary']:
                result['today_summary'] = entry.content

    except Exception as e:
        logger.warning("Error querying L2 MemoryEntry for user %s: %s", user, e)

    return result


def search_memories(
    user,
    query: str,
    limit: int = 5,
    level: Optional[int] = None,
    memory_type: Optional[str] = None,
) -> list:
    """全文搜索用户的记忆条目。

    使用 django.contrib.postgres.search 的 SearchVector 和 SearchQuery
    进行动态全文搜索。搜索范围包括 content 和 metadata 字段。

    Args:
        user: User 模型实例。
        query: 搜索关键词。
        limit: 返回结果上限，默认 5。
        level: 可选，按记忆级别筛选 (1/2/3)。
        memory_type: 可选，按记忆类型筛选。

    Returns:
        list[dict]: 按相关性得分降序排列，每项包含:
            id, level, memory_type, content, metadata, weight, created_at, score.
    """
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

    from infra.llm.models import MemoryEntry

    try:
        # NOTE: config='simple' is English-optimized. For Chinese text search,
        # install zhparser (https://github.com/amutu/zhparser) and set
        # search_config to 'zh' or 'chinese' dynamically.
        search_config = 'simple'
        vector = SearchVector('content', config=search_config)
        search_query = SearchQuery(query, config=search_config)

        queryset = MemoryEntry.objects.filter(user=user, is_active=True)

        if level is not None:
            queryset = queryset.filter(level=level)
        if memory_type is not None:
            queryset = queryset.filter(memory_type=memory_type)

        queryset = (
            queryset
            .annotate(rank=SearchRank(vector, search_query))
            .filter(rank__gte=0.1)
            .order_by('-rank', '-weight')
        )[:limit]

        entries = list(queryset)
        if entries:
            pks = [e.pk for e in entries]
            MemoryEntry.objects.filter(pk__in=pks).update(
                access_count=models.F('access_count') + 1,
                accessed_at=timezone.now(),
            )

        results = []
        for entry in entries:
            results.append({
                'id': entry.pk,
                'level': entry.level,
                'memory_type': entry.memory_type,
                'content': entry.content,
                'metadata': entry.metadata,
                'weight': entry.weight,
                'created_at': entry.created_at.isoformat(),
                'score': float(getattr(entry, 'rank', 0) or 0),
            })

        return results

    except Exception as e:
        logger.warning(
            "Error searching memories for user %s (query=%r): %s", user, query, e
        )
        return []


def store_memory(
    user,
    level: int,
    memory_type: str,
    content: str,
    metadata: Optional[dict] = None,
    weight: float = 1.0,
    expires_at: Optional[datetime] = None,
):
    """存储一条新的记忆条目。

    对于 memory_type='persona_summary' 且 level=1 的情况，
    先将所有旧的同类型有效记录置为无效，再创建新记录。

    Args:
        user: User 模型实例。
        level: 记忆级别 (1/2/3)。
        memory_type: 记忆类型。
        content: 记忆内容文本。
        metadata: 可选的元数据字典。
        weight: 权重 (0-10)，默认 1.0。
        expires_at: 可选过期时间。

    Returns:
        MemoryEntry: 新创建的记忆条目，失败时返回 None。
    """
    from infra.llm.models import MemoryEntry

    # 标准化 metadata
    meta = dict(metadata or {})
    meta.setdefault('source', 'memory_service')

    try:
        # Dedup: 如果存在完全相同的活跃条目，更新权重并返回
        existing = MemoryEntry.objects.filter(
            user=user,
            level=level,
            memory_type=memory_type,
            content=content,
            is_active=True,
        ).first()

        if existing is not None:
            existing.weight = max(existing.weight, weight)
            existing.accessed_at = timezone.now()
            if metadata:
                existing.metadata.update(metadata)
            existing.save(update_fields=['weight', 'accessed_at', 'metadata'])
            return existing

        # persona_summary + level=1: 先失效旧记录
        if memory_type == 'persona_summary' and level == 1:
            with transaction.atomic():
                updated = MemoryEntry.objects.filter(
                    user=user,
                    level=1,
                    memory_type='persona_summary',
                    is_active=True,
                ).update(is_active=False)
                if updated:
                    logger.info(
                        "Deactivated %d old persona_summary entries for user %s",
                        updated, user,
                    )

                entry = MemoryEntry.objects.create(
                    user=user,
                    level=level,
                    memory_type=memory_type,
                    content=content,
                    metadata=meta,
                    weight=weight,
                    expires_at=expires_at,
                )
            return entry

        entry = MemoryEntry.objects.create(
            user=user,
            level=level,
            memory_type=memory_type,
            content=content,
            metadata=meta,
            weight=weight,
            expires_at=expires_at,
        )
        return entry

    except Exception as e:
        logger.error(
            "Failed to store memory for user %s (level=%s, type=%s): %s",
            user, level, memory_type, e,
        )
        return None


def deactivate_expired() -> int:
    """将已过期的记忆条目置为无效。

    查询所有 expires_at <= 当前时间 且 is_active=True 的记录，
    批量设置为 is_active=False。

    适合 Celery 定时任务调度。

    Returns:
        int: 被失效的记录总数。
    """
    from infra.llm.models import MemoryEntry

    try:
        result = MemoryEntry.objects.filter(
            expires_at__lte=timezone.now(),
            is_active=True,
        ).update(is_active=False, accessed_at=timezone.now())
        return result
    except Exception as e:
        logger.error("Failed to deactivate expired memories: %s", e)
        return 0


def get_memory_stats(user) -> dict:
    """获取用户的记忆条目统计信息。

    Args:
        user: User 模型实例。

    Returns:
        dict: {
            'total': int,                              # 总有效条目数
            'by_level': {1: int, 2: int, 3: int},      # 按级别统计
            'by_type': {str: int, ...},                 # 按类型统计
            'active_expired': int,                      # 已过期但仍有效的条目数
        }
    """
    from infra.llm.models import MemoryEntry

    stats = {
        'total': 0,
        'by_level': {1: 0, 2: 0, 3: 0},
        'by_type': {},
        'active_expired': 0,
    }

    try:
        # 总有效条目数
        stats['total'] = MemoryEntry.objects.filter(
            user=user, is_active=True
        ).count()

        # 按级别统计
        level_counts = (
            MemoryEntry.objects
            .filter(user=user, is_active=True)
            .values('level')
            .annotate(count=Count('pk'))
        )
        for item in level_counts:
            stats['by_level'][item['level']] = item['count']

        # 按类型统计
        type_counts = (
            MemoryEntry.objects
            .filter(user=user, is_active=True)
            .values('memory_type')
            .annotate(count=Count('pk'))
        )
        for item in type_counts:
            stats['by_type'][item['memory_type']] = item['count']

        # 已过期但仍有效
        stats['active_expired'] = MemoryEntry.objects.filter(
            user=user,
            expires_at__lte=timezone.now(),
            is_active=True,
        ).count()

    except Exception as e:
        logger.warning("Error getting memory stats for user %s: %s", user, e)

    return stats


__all__ = [
    'get_level1_profile',
    'get_level2_context',
    'search_memories',
    'store_memory',
    'deactivate_expired',
    'get_memory_stats',
]
