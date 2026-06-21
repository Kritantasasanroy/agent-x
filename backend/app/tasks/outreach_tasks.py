"""Celery tasks for recruiter outreach (daily)."""

from __future__ import annotations

from app.agents.outreach import OutreachAgent
from app.core.celery_app import celery
from app.db import session as db_session


@celery.task(name="app.tasks.outreach_tasks.run_outreach")
def run_outreach() -> dict:
    with OutreachAgent() as agent:
        sent = agent.process_followups()
    return {"followups_sent": sent}


@celery.task(name="app.tasks.outreach_tasks.start_sequence")
def start_sequence(user_id: str, recruiter_id: str, job_id: str | None = None) -> dict:
    from app.db.models import Job, Profile, Recruiter

    db = db_session.session()
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).one_or_none()
        recruiter = db.get(Recruiter, recruiter_id)
        job = db.get(Job, job_id) if job_id else None
        if not profile or not recruiter:
            return {"error": "missing profile or recruiter"}
        agent = OutreachAgent(db)
        msg = agent.queue_initial(recruiter, profile, job)
        # schedule follow-ups
        agent._create_step(recruiter, profile, job, step=1, send_now=False)
        agent._create_step(recruiter, profile, job, step=2, send_now=False)
        return {"message_id": msg.id}
    finally:
        db.close()
