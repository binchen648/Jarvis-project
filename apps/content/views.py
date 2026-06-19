import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ProcessedContent, UserSubmittedContent

logger = logging.getLogger(__name__)


@login_required
def feed(request):
    """推荐列表页 — HTMX 就绪"""
    try:
        from .recommender import get_recommendations_for_user
        content_ids = get_recommendations_for_user(request.user, limit=20)
        # Preserve recommendation ranking order (filter(id__in=...) does NOT guarantee order)
        content_map = ProcessedContent.objects.in_bulk(content_ids)
        contents = [content_map[cid] for cid in content_ids if cid in content_map]
    except ImportError:
        # Fallback if recommender not available
        contents = ProcessedContent.objects.filter(stage='active')[:20]
    
    # Mark bookmarked content for highlight in template
    bookmarked_ids = set()
    if request.user.is_authenticated:
        from .models import UserSubmittedContent
        bookmarked_urls = set(
            UserSubmittedContent.objects.filter(
                submitted_by=request.user, is_active=True
            ).values_list('url', flat=True)
        )
        bookmarked_ids = {c.id for c in contents if c.url in bookmarked_urls}
    
    return render(request, 'content/feed.html', {
        'contents': contents,
        'bookmarked_ids': bookmarked_ids,
    })


@login_required
def detail(request, content_id):
    """内容详情页"""
    content = get_object_or_404(ProcessedContent, id=content_id)
    return render(request, 'content/detail.html', {
        'content': content,
    })


@login_required
@require_POST
def interact(request, content_id):
    """内容交互: bookmark / block / read
    POST data: {"action": "bookmark"|"block"|"read"}
    """
    content = get_object_or_404(ProcessedContent, id=content_id)
    action = request.POST.get('action')
    
    if action not in ('bookmark', 'block', 'read'):
        return HttpResponseBadRequest("Invalid action")

    if action == 'bookmark':
        from .models import UserSubmittedContent
        UserSubmittedContent.objects.get_or_create(
            url=content.url,
            submitted_by=request.user,
            defaults={
                'title': content.title,
                'body_text': content.description,
                'summary': content.ai_summary or content.description[:500],
            }
        )
        logger.info("User %s bookmarked content %s (persisted)", request.user, content_id)
    else:
        logger.info("User %s %s content %s (no persistence needed)", request.user, action, content_id)

    return JsonResponse({"status": "ok", "action": action, "content_id": content_id})


@login_required
def submit_url(request):
    """用户提交 URL 内容 (GET: 表单, POST: 创建 + 触发抓取)."""
    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        if not url:
            messages.error(request, '请填写 URL')
            return render(request, 'content/submit_url.html')
        item = UserSubmittedContent.objects.create(
            url=url,
            submitted_by=request.user,
        )
        # Trigger async fetch task
        from .tasks import fetch_url_content
        fetch_url_content.delay(item.id)  # pyright: ignore[reportCallIssue]
        messages.success(request, '内容已提交，正在抓取...')
        return redirect('content:submitted_list')
    return render(request, 'content/submit_url.html')


@login_required
def submitted_list(request):
    """用户已提交的 URL 列表."""
    items = UserSubmittedContent.objects.filter(submitted_by=request.user)
    return render(request, 'content/submitted_list.html', {
        'items': items,
    })
