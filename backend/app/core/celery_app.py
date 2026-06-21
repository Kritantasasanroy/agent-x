"""Celery application + beat schedule (the autonomous scheduler)."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "jobhunter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.discovery_tasks",
        "app.tasks.application_tasks",
        "app.tasks.outreach_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.learning_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
)

# ---- The schedule the brief asked for ----
celery.conf.beat_schedule = {
    "job-discovery-every-30m": {
        "task": "app.tasks.discovery_tasks.run_discovery",
        "schedule": 30 * 60,
    },
    "application-processing-every-15m": {
        "task": "app.tasks.application_tasks.process_applications",
        "schedule": 15 * 60,
    },
    "recruiter-outreach-daily": {
        "task": "app.tasks.outreach_tasks.run_outreach",
        "schedule": crontab(hour=9, minute=0),
    },
    "analytics-daily": {
        "task": "app.tasks.analytics_tasks.refresh_analytics",
        "schedule": crontab(hour=1, minute=0),
    },
    "learning-weekly": {
        "task": "app.tasks.learning_tasks.run_learning",
        "schedule": crontab(hour=2, minute=0, day_of_week="sun"),
    },
}
