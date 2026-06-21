"""Celery tasks for analytics refresh (daily)."""

from __future__ import annotations

from app.agents.pipeline import cleanup_stale
from app.agents.tracking import TrackingAgent
from app.core.celery_app import celery
from app.db import session as db_session


@celery.task(name="app.tasks.analytics_tasks.refresh_analytics")
def refresh_analytics() -> dict:
    with TrackingAgent() as agent:
        snapshot = agent.analytics()
        agent.audit("analytics_refresh", **{k: v for k, v in snapshot.items() if isinstance(v, int | float)})
    db = db_session.session()
    try:
        removed = cleanup_stale(db)
    finally:
        db.close()
    return {"snapshot": snapshot, "stale_removed": removed}
