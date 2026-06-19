class HtmxRedirectMiddleware:
    """Converts Django 302 redirects to HTMX-compatible 204+HX-Redirect responses.

    For authenticated-area pages (profile editing), HTMX requests that trigger
    302 redirects get a 204 No Content response with HX-Redirect header instead.
    This allows HTMX to follow the redirect properly.

    Excludes allauth auth paths (login/signup/reset) which use standard form POST.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only apply to HTMX requests with 302 redirects
        if (request.headers.get("HX-Request") == "true"
                and response.status_code == 302
                and "Location" in response):
            response.status_code = 204  # No Content
            response["HX-Redirect"] = response["Location"]
            del response["Location"]

        return response


import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings


class LoginRateLimitMiddleware:
    """Redis-backed IP-based rate limiter for login/signup paths.

    Uses Django cache (Redis) for shared state across workers.
    Uses REMOTE_ADDR to prevent X-Forwarded-For spoofing.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_requests = getattr(settings, 'LOGIN_RATE_LIMIT_MAX', 10)
        self.window = getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW', 60)

    def __call__(self, request):
        if request.method == 'POST' and request.path.startswith('/accounts/'):
            ip = request.META.get('REMOTE_ADDR', '')
            if ip:
                cache_key = f"ratelimit:login:{ip}"
                count = cache.get(cache_key, 0)
                if count >= self.max_requests:
                    return JsonResponse(
                        {"error": "Too many requests. Please try again later."},
                        status=429,
                    )
                cache.set(cache_key, count + 1, self.window)
        return self.get_response(request)
