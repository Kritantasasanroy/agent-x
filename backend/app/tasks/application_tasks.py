"""Celery tasks for application processing (every 15 min)."""

from __future__ import annotations

from app.agents.pipeline import detect_responses_and_prep, process_user_applications
from app.core.celery_app import celery
from app.db import session as db_session
from app.db.models import User


@celery.task(name="app.tasks.application_tasks.process_applications")
def process_applications() -> dict:
    db = db_session.session()
    out: dict[str, dict] = {}
    try:
        for user in db.query(User).filter(User.is_active.is_(True)).all():
            out[user.email] = process_user_applications(db, user)
        out["prepped"] = {"interviews": detect_responses_and_prep(db)}
    finally:
        db.close()
    return out


@celery.task(name="app.tasks.application_tasks.apply_to_job")
def apply_to_job(user_id: str, job_id: str, auto_submit: bool = True) -> dict:
    """On-demand single application triggered from the UI."""
    from app.agents.application import ApplicationAgent
    from app.agents.cover_letter import CoverLetterAgent
    from app.agents.resume import ResumeAgent
    from app.db.models import Application, ApplicationStatus, Job, Profile

    db = db_session.session()
    try:
        job = db.get(Job, job_id)
        profile = db.query(Profile).filter(Profile.user_id == user_id).one_or_none()
        if not job or not profile:
            return {"error": "missing job or profile"}
        resume = ResumeAgent(db).run(job, profile, variant="A")
        cover = CoverLetterAgent(db).run(job, profile)
        app = Application(
            user_id=user_id, job_id=job_id, resume_id=resume.id,
            cover_letter_id=cover.id, status=ApplicationStatus.pending,
        )
        db.add(app)
        db.commit()
        ApplicationAgent(db).run(app, auto_submit=auto_submit)
        return {"application_id": app.id, "status": str(app.status)}
    finally:
        db.close()
