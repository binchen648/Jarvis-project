# 生产就绪修复计划

## Goal
修复 Jarvis 项目 6 项 P0 + 2 项 P1 生产就绪问题

## Parallel Groups

### Group A: Config Hardening
Files: `config/settings/base.py`, `.env.example`
Changes:
- Add SMTP email config (EMAIL_HOST/PORT/USER/PASSWORD, dev defaults to console)
- ALLOWED_HOSTS default → `['localhost', '127.0.0.1', '::1']`
- Add CSRF_TRUSTED_ORIGINS config from env
- Add CONN_MAX_AGE = 600
- Add LOGGING dictConfig (console + file rotation)

### Group B: Health Check + Rate Limit
Files: `config/urls.py`, `config/settings/base.py`, new `apps/health/` app
Changes:
- Create `apps/health/views.py` — returns `{"status":"ok","database":"ok","redis":"ok"}`
- Create `apps/health/urls.py` — route `/health/`
- Create `apps/health/apps.py`, `__init__.py`
- Register `apps.health` in INSTALLED_APPS
- Add rate limit middleware to `apps/accounts/middleware.py` (IP-based, login/signup paths, 10req/min)

### Group C: Sentry + Whitenoise
Files: `config/settings/base.py`, `config/settings/prod.py`, `requirements.txt`
Changes:
- Add `sentry-sdk` and `whitenoise` to requirements.txt
- Add whitenoise middleware to MIDDLEWARE (after SecurityMiddleware)
- Add Sentry SDK init (conditional on SENTRY_DSN env var)
- Add STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' in prod.py
