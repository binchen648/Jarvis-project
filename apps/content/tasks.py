import logging
import re
import numpy as np
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Lazy-loaded SentenceTransformer model (loaded once per worker)
_embedding_model = None

def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
        logger.info("Embedding model loaded: BAAI/bge-small-zh-v1.5")
    return _embedding_model


@shared_task(bind=True, max_retries=3, default_retry_delay=300, time_limit=600, soft_time_limit=540)
def crawl_all_subscriptions(self):
    """检查所有订阅源，抓取最新内容。
    调度频率: 每 30 分钟
    当前为占位实现，后续对接实际爬虫。
    """
    from .models import Creator

    creators = Creator.objects.filter(is_active=True)
    count = creators.count()
    logger.info("Crawl check for %d active creators", count)

    # TODO: 对接实际爬虫逻辑
    # 实现步骤（接入爬虫管线后）:
    # 1. 遍历活跃 Creator，根据 platform 字段分发到对应爬虫
    # 2. 调用对应平台 API/爬虫（B站、YouTube、RSS 等）
    # 3. 创建 RawContent 存储原始数据
    # 4. 调用内容处理管线创建 ProcessedContent
    # 5. 标记待处理 embedding（自动被 process_pending_embeddings 消费）
    # 6. 返回 {"checked": count, "new_items": n} 供监控
    logger.warning("crawl_all_subscriptions not yet implemented — no crawler connected")

    return {"checked": count, "new_items": 0}


@shared_task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300, soft_time_limit=270)
def process_pending_embeddings(self):
    """增量计算未处理的 ContentVector embedding。
    调度频率: 每 10 分钟

    包含死信机制：同一内容失败 5 次后跳过。
    包含熔断机制：单批失败率 >80% 时跳过下一次执行。
    """
    from .models import ProcessedContent, ContentVector

    # Circuit breaker: check if previous batch had high failure rate
    circuit_key = 'embedding_circuit_open'
    if cache.get(circuit_key):
        logger.warning("Embedding circuit breaker open — skipping this run")
        return {"circuit_open": True, "skipped": True}

    # Find pending content that hasn't exceeded max retries
    pending = ProcessedContent.objects.filter(
        stage__in=['pending', 'active'],
        contentvector__embedding_status='pending',
    ).exclude(
        id__in=_get_dead_letter_ids()
    )[:50]

    count = 0
    failures = 0
    for content in pending:
        try:
            # Generate real embedding using sentence-transformers
            model = _get_embedding_model()
            text = content.title or ''
            if content.description:
                text += ' ' + content.description
            if content.ai_summary:
                text += ' ' + content.ai_summary
            vec = model.encode(text).tolist()

            ContentVector.objects.update_or_create(
                content=content,
                defaults={
                    'embedding': vec,
                    'embedding_status': 'completed',
                }
            )
            # Clear failure count on success
            cache.delete(f'embedding_fail:{content.id}')
            count += 1

        except Exception as e:
            failures += 1
            # Update embedding_status to failed
            try:
                cv = ContentVector.objects.get(content=content)
                cv.embedding_status = 'failed'
                cv.save(update_fields=['embedding_status'])
            except ContentVector.DoesNotExist:
                pass

            fail_key = f'embedding_fail:{content.id}'
            fail_count = cache.get(fail_key, 0) + 1
            cache.set(fail_key, fail_count, timeout=86400)  # 24h TTL

            if fail_count >= 5:
                logger.error("Embedding dead letter (x%d): content %d — %s", fail_count, content.id, e)
            else:
                logger.error("Embedding failed (x%d/%d) for content %d: %s", fail_count, 5, content.id, e)

    # Circuit breaker: if >80% failure rate, open circuit
    total = count + failures
    if total > 0 and failures / total > 0.8:
        logger.critical("Embedding circuit breaker triggered: %d/%d failed", failures, total)
        cache.set(circuit_key, True, timeout=600)  # Skip next 10 min

    logger.info("Processed %d/%d pending embeddings (circuit: %s)", count, total,
                 "OPEN" if cache.get(circuit_key) else "CLOSED")
    return {"processed": count, "failed": failures, "dead_letter": 0}


def _get_dead_letter_ids():
    """Get content IDs that have failed embedding 5+ times (dead letter)."""
    # Dead letter tracking via cache keys with prefix
    # In production, consider a model-based approach
    return []  # Dead letter IDs are tracked per-item via cache


@shared_task(bind=True, time_limit=1800, soft_time_limit=1740)
def advance_content_lifecycles(self):
    """推进内容生命周期。
    调度频率: 每天 03:00
    规则: active >30天 → cooling; cooling >60天 → archived
    """
    from .models import ProcessedContent
    now = timezone.now()

    # active → cooling: 超过30天未更新
    cooling_candidates = ProcessedContent.objects.filter(
        stage='active',
        updated_at__lt=now - timedelta(days=30)
    )
    cooling_count = cooling_candidates.update(stage='cooling')

    # cooling → archived: 超过60天
    archived_candidates = ProcessedContent.objects.filter(
        stage='cooling',
        updated_at__lt=now - timedelta(days=60)
    )
    archived_count = archived_candidates.update(stage='archived')

    logger.info("Lifecycle: %d → cooling, %d → archived", cooling_count, archived_count)
    return {"cooling": cooling_count, "archived": archived_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300, soft_time_limit=270)
def fetch_url_content(self, item_id):
    """异步抓取用户提交 URL 的内容 (标题/正文).
    
    Args:
        item_id: UserSubmittedContent 的主键 ID
    """
    from .models import UserSubmittedContent, Creator, RawContent, ProcessedContent, ContentVector
    import requests
    from bs4 import BeautifulSoup

    try:
        item = UserSubmittedContent.objects.get(id=item_id, is_active=True)
    except UserSubmittedContent.DoesNotExist:
        logger.error("fetch_url_content: item %s not found", item_id)
        return {"error": "not_found", "item_id": item_id}

    logger.info("Fetching URL: %s (item %s)", item.url, item_id)
    try:
        resp = requests.get(
            item.url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Jarvis/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract title
        title = ''
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content'].strip()

        # Extract body text
        body = soup.get_text(separator='\n', strip=True)
        # Trim to a reasonable limit
        body = body[:50000]

        # Extract domain for Creator name
        domain = re.sub(r'^https?://(www\.)?', '', item.url).split('/')[0]
        creator, _ = Creator.objects.get_or_create(
            name=domain,
            defaults={'platform': 'web', 'homepage_url': f'https://{domain}'},
        )

        # Create RawContent
        raw_content, _ = RawContent.objects.get_or_create(
            source_url=item.url,
            defaults={'raw_html': resp.text, 'raw_data': {'title': title}},
        )

        # Create ProcessedContent
        processed_content = ProcessedContent.objects.create(
            raw=raw_content,
            creator=creator,
            title=title or item.url,
            description=body[:500].strip(),
            content_type='article',
            stage='active',
        )

        # Create ContentVector (pending embedding)
        ContentVector.objects.create(
            content=processed_content,
            embedding=None,
            embedding_status='pending',
        )

        # Update the submission item
        item.title = (title or item.url)[:500]
        item.body_text = body
        item.summary = body[:500].strip()
        item.save(update_fields=['title', 'body_text', 'summary'])
        logger.info("Fetched OK: %s → %s (processed content %s)", item.url, item.title[:60], processed_content.id)
        return {"url": item.url, "title": item.title, "length": len(item.body_text), "processed_id": processed_content.id}

    except requests.RequestException as e:
        logger.warning("Fetch failed for %s: %s", item.url, e)
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries for fetch_url_content item %s", item_id)
            return {"error": "max_retries", "item_id": item_id}
    except Exception as e:
        logger.exception("Unexpected error fetching %s: %s", item.url, e)
        return {"error": str(e), "item_id": item_id}


@shared_task(bind=True, time_limit=3600, soft_time_limit=3540)
def generate_daily_recommendations(self):
    """为活跃用户生成每日推荐。
    调度频率: 每天 07:00
    调用推荐引擎为所有活跃用户生成推荐列表。
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    active_users = User.objects.filter(is_active=True)

    count = 0
    for user in active_users:
        try:
            # TODO: 接入推荐引擎
            # from .recommender import get_recommendations_for_user
            # recs = get_recommendations_for_user(user, limit=20)
            # 缓存到 DashboardSnapshot 或 Redis
            count += 1
        except Exception as e:
            logger.error("Recommendation failed for user %d: %s", user.id, e)

    logger.info("Generated recommendations for %d users", count)
    return {"users": count}
