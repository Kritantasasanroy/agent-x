"""Celery tasks for discovery + analysis (every 30 min)."""

from __future__ import annotations

from app.agents.discovery import DiscoveryAgent
from app.agents.pipeline import analyze_new_jobs
from app.core.celery_app import celery
from app.db import session as db_session
from app.db.models import Profile


@celery.task(name="app.tasks.discovery_tasks.run_discovery")
def run_discovery(queries: list[str] | None = None) -> dict:
    with DiscoveryAgent() as agent:
        result = agent.run(queries=queries)
    # analyze against every profile that exists
    db = db_session.session()
    try:
        analyzed = 0
        for profile in db.query(Profile).all():
            analyzed += analyze_new_jobs(db, profile)
        result["analyzed"] = analyzed
    finally:
        db.close()
    return result
