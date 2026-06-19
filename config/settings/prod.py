from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False

# Security: reject insecure defaults
if SECRET_KEY.startswith('django-insecure'):
    raise ImproperlyConfigured("SECRET_KEY must not be the default insecure value in production")
if '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be explicitly set in production")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'

# Static files (Whitenoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Redis password guard
_redis_url = config('REDIS_URL', default='')
if not _redis_url or 'redispass' in _redis_url:
    raise ImproperlyConfigured("REDIS_URL must use a strong password in production")
