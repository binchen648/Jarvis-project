import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.timezone = 'Asia/Shanghai'

app.conf.beat_schedule = {
    'crawl-all-subscriptions': {
        'task': 'apps.content.tasks.crawl_all_subscriptions',
        'schedule': 1800.0,  # every 30 minutes
    },
    'process-pending-embeddings': {
        'task': 'apps.content.tasks.process_pending_embeddings',
        'schedule': crontab(minute='*/10'),  # every 10 minutes
    },
    'advance-content-lifecycles': {
        'task': 'apps.content.tasks.advance_content_lifecycles',
        'schedule': crontab(hour=3, minute=0),  # daily at 03:00
    },
    'generate-daily-recommendations': {
        'task': 'apps.content.tasks.generate_daily_recommendations',
        'schedule': crontab(hour=7, minute=0),  # daily at 07:00
    },
    # Phase 3 — goals
    'check-goal-deadlines': {
        'task': 'apps.goals.tasks.check_goal_deadlines',
        'schedule': crontab(hour=8, minute=0),  # daily 08:00
    },
    'aggregate-daily-sessions': {
        'task': 'apps.goals.tasks.aggregate_daily_sessions',
        'schedule': crontab(hour=0, minute=30),  # daily 00:30
    },
    # Phase 3 — wellness
    'generate-health-suggestions': {
        'task': 'apps.wellness.tasks.generate_health_suggestions',
        'schedule': crontab(hour=20, minute=0),  # daily at 20:00
    },
    # Phase 3 — trajectory
    'update-skill-stats': {
        'task': 'apps.trajectory.tasks.update_skill_stats',
        'schedule': crontab(hour=3, minute=0),  # daily 03:00
    },
    'check-path-progress': {
        'task': 'apps.trajectory.tasks.check_path_progress',
        'schedule': crontab(hour=8, minute=30),  # daily 08:30
    },
    # Phase 4 — persona
    'build-all-personas': {
        'task': 'infra.llm.tasks.build_all_personas',
        'schedule': crontab(hour='*/6'),  # every 6 hours
    },
    # Event bus — advance pending events
    'process_events': {
        'task': 'infra.eventbus.tasks.process_pending_events',
        'schedule': 60.0,  # every 60 seconds
        'options': {'queue': 'default'},
    },
    # Surface — evening summaries
    'build-evening-summaries': {
        'task': 'infra.surface.tasks.build_evening_summaries',
        'schedule': crontab(hour=21, minute=0),  # daily 21:00
    },
}
