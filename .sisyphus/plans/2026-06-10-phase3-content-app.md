# Phase 3 — content App 实施计划

## Goal
实现 content App 的完整内容抓取与推荐管线

## Dependencies
```
Task 1 (Models + Migration)
  ├── Task 2 (Celery Tasks — crawl/embed/lifecycle/recommend)
  ├── Task 3 (Recommendation Engine — recall + rank)
  ├── Task 4 (Views + URLs + Templates)
  └── Task 5 (Tests)
Task 6 (Celery Beat config) — independent
```

## Tasks

### Task 1: Models + Migration + Admin
Files: `apps/content/models.py`, `apps/content/admin.py`, migration
- RawContent, ProcessedContent, ContentVector models
- PgVector extension in migration (CREATE EXTENSION IF NOT EXISTS vector)
- Register all 3 models in admin.py
- makemigrations

### Task 2: Content Processing Celery Tasks
File: `apps/content/tasks.py`
- crawl_all_subscriptions — placeholder crawl logic
- process_pending_embeddings — compute embeddings via pgvector
- advance_content_lifecycles — lifecycle state machine
- generate_daily_recommendations — trigger recommendation engine

### Task 3: Recommendation Engine
File: `apps/content/recommender.py`
- 4 Recall methods (subscription, similar/vector, trending, explore)
- 3-Tier ranking (coarse rules → fine weighted → LLM re-rank placeholder)
- Cold start strategy (Stage 0-3)
- get_recommendations_for_user(user, limit=20) entry point

### Task 4: Views + URLs + Templates
Files: `apps/content/views.py`, `apps/content/urls.py`, templates
- GET /content/feed/ — HTMX-ready recommendation list
- GET /content/<id>/ — content detail
- POST /content/<id>/interact/ — bookmark/block/read

### Task 5: Tests
File: `apps/content/tests.py`
- Model tests for all 3 models
- Recommender unit tests (mock recalls)

### Task 6: Celery Beat Schedule
File: `config/celery.py`
- Register beat_schedule for crawl, embed, lifecycle, recommend tasks
