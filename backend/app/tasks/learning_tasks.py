"""Celery tasks for the learning agent (weekly)."""

from __future__ import annotations

from app.agents.learning import LearningAgent
from app.core.celery_app import celery
from app.db import session as db_session
from app.db.models import User


@celery.task(name="app.tasks.learning_tasks.run_learning")
def run_learning() -> dict:
    db = db_session.session()
    out: dict[str, dict] = {}
    try:
        agent = LearningAgent(db)
        for user in db.query(User).all():
            out[user.email] = agent.run(user.id)
    finally:
        db.close()
    return out
