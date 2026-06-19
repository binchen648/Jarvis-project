# Phase 2: User Authentication System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build complete user authentication system with django-allauth 65.x, including login/signup/password-reset flows and user profile management.

**Architecture:** Allauth handles core auth (login, signup, password reset) with project template overrides for Chinese-locale UI. Custom views handle user profile editing with HTMX progressive enhancement. Signals auto-create UserProfile on signup. Standard Django forms for auth pages (no HTMX on login/signup — minimal UX gain, significant redirect complexity).

**Tech Stack:** Django 5.0.14, django-allauth 65.18.0, HTMX 2.x, Daphne/Channels, PostgreSQL 15

**Key Constraints:**
- Allauth 65.x → use new API (`ACCOUNT_LOGIN_METHODS`, `ACCOUNT_SIGNUP_FIELDS`), NOT deprecated `ACCOUNT_AUTHENTICATION_METHOD`
- 64.0+ is ASGI/Daphne compatible — no AccountMiddleware patching needed
- Template overrides extend project `base.html` directly — DO NOT use allauth's element system
- Auth pages use standard Django POST (no HTMX) — profile editing uses HTMX
- All template strings use `{% trans %}` for zh-hans locale
- Import signals with `dispatch_uid` in `apps.py ready()`

---

### Task 1: Allauth Settings + Template Dir Config

**Files:**
- Modify: `config/settings/base.py`
- Modify: `config/settings/dev.py`

**Step 1: Update base.py**

Add after line 131 (end of file):

```python
# django-allauth configuration
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# Authentication URLs
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

# Email (dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Change TEMPLATES DIRS from `[]` to:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        ...
    },
]
```

**Step 2: Create templates/ directory**

```bash
mkdir -p templates/account templates/userprofile
```

**Step 3: Update dev.py** — already has `ALLOWED_HOSTS = ['*']` and `DEBUG = True`, no auth-specific changes needed.

**Step 4: Run validation**

```bash
cd "D:\Jarvis project"
.venv\Scripts\python manage.py check --settings=config.settings.dev
# Expected: System check identified no issues (0 silenced)
```

---

### Task 2: Project Base Template

**Files:**
- Create: `templates/base.html`

Base template with HTMX, nav bar, user menu, and content block. Must include:
- HTMX script (CDN or bundled)
- CSRF header for HTMX (`hx-headers`)
- Navigation with user menu (login/logout/profile links, conditionally shown)
- `{% block content %}` for child templates
- Chinese language meta tag
- Project name "Jarvis" in header
- Django messages display block

---

### Task 3: Allauth Template Overrides

**Files:**
- Create: `templates/account/login.html`
- Create: `templates/account/signup.html`
- Create: `templates/account/logout.html`
- Create: `templates/account/password_reset.html`
- Create: `templates/account/password_reset_done.html`
- Create: `templates/account/password_reset_from_key.html`
- Create: `templates/account/password_reset_from_key_done.html`

Each template:
- Extends `base.html`
- Uses `{% trans %}` for all visible strings
- Uses `{% crispy %}` or standard `{{ form.as_p }}` with custom CSS classes
- Login: username field, password field, remember me checkbox, submit button, signup link
- Signup: username, email, password1, password2 fields, submit button, login link
- Password reset: email field, submit button
- Error messages displayed above form

---

### Task 4: HTMX Redirect Middleware

**Files:**
- Create: `apps/accounts/middleware.py`

Allauth views return 302 redirects. With HTMX requests, 302 is swallowed (not followed). Add middleware that converts 302 to 204 + `HX-Redirect` header for HTMX requests.

```python
# accounts/middleware.py
class HtmxRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.headers.get("HX-Request") == "true" and response.status_code == 302:
            response.status_code = 204
            response["HX-Redirect"] = response["Location"]
            del response["Location"]
        return response
```

Only applies to authenticated-area pages (profile edit), NOT to auth forms (login/signup use standard POST).

**Add to MIDDLEWARE in base.py:**
```python
MIDDLEWARE = [
    ...
    'apps.accounts.middleware.HtmxRedirectMiddleware',
]
```

---

### Task 5: UserProfile Auto-Creation Signal

**Files:**
- Create: `apps/accounts/signals.py`
- Modify: `apps/accounts/apps.py`

Use allauth's `user_signed_up` signal instead of Django's `post_save`:
- Prevents profile creation for admin-created users (signals only fires on actual signup)
- Avoids race condition with email verification flow

```python
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django.conf import settings


@receiver(user_signed_up, dispatch_uid="create_user_profile_on_signup")
def create_user_profile(sender, **kwargs):
    user = kwargs["user"]
    from apps.userprofile.models import UserProfile
    UserProfile.objects.get_or_create(user=user)
```

```python
# apps/accounts/apps.py
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        import apps.accounts.signals  # noqa
```

---

### Task 6: User Profile Views & Templates

**Files:**
- Modify: `apps/accounts/views.py`
- Create: `apps/accounts/urls.py`
- Modify: `config/urls.py`
- Create: `templates/userprofile/profile_detail.html`
- Create: `templates/userprofile/profile_edit.html`

**Views:**
- `ProfileDetailView` (LoginRequiredMixin, DetailView): Shows user info, preferences, settings
- `ProfileEditView` (LoginRequiredMixin, UpdateView): Edit profile with HTMX form submission

**URLs (apps/accounts/urls.py):**
```python
urlpatterns = [
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
]
```

**Root URLs (config/urls.py):**
Add: `path('', include('apps.accounts.urls'))`

---

### Task 7: Tests

**Files:**
- Modify: `apps/accounts/tests.py`
- Create: `apps/userprofile/tests.py`

**Test scenarios:**
1. GET /accounts/signup/ returns 200 with signup form
2. POST /accounts/signup/ with valid data creates User + UserProfile
3. POST /accounts/signup/ with missing fields returns form errors
4. GET /accounts/login/ returns 200 with login form
5. POST /accounts/login/ with valid credentials redirects to /
6. POST /accounts/login/ with invalid credentials returns form errors
7. GET /profile/ returns 200 (authenticated user)
8. GET /profile/ redirects to login (anonymous user)
9. POST /profile/edit/ with valid data updates profile
10. UserProfile auto-created on signup signal fires

---

### Task 8: Final Verification

Run in sequence:

```bash
cd "D:\Jarvis project"
.venv\Scripts\python manage.py check --settings=config.settings.dev
# Expected: 0 issues

.venv\Scripts\python manage.py test --settings=config.settings.dev
# Expected: Pass

.venv\Scripts\python manage.py runserver 0.0.0.0:8000
# Manual: visit /accounts/login/ -> styled login page
# Manual: visit /accounts/signup/ -> styled signup page
# Manual: signup -> redirect to / -> user menu shows profile link
# Manual: visit /profile/ -> shows user info
# Manual: visit /profile/edit/ -> edit form with HTMX
```
