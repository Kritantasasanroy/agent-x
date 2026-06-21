"""Orchestration helpers chaining agents into end-to-end flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.agents.analysis import AnalysisAgent
from app.agents.application import ApplicationAgent
from app.agents.cover_letter import CoverLetterAgent
from app.agents.resume import ResumeAgent
from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import (
    Application,
    ApplicationStatus,
    CompanyRule,
    Job,
    Profile,
    User,
)

log = get_logger("pipeline")


def _blacklisted(db: Session, company: str) -> bool:
    rule = db.query(CompanyRule).filter(CompanyRule.company.ilike(company)).one_or_none()
    if not rule:
        # if any whitelist exists, only whitelisted companies pass
        wl = db.query(CompanyRule).filter(CompanyRule.kind == "whitelist").count()
        if wl:
            return True
        return False
    return rule.kind == "blacklist"


def _applied_today(db: Session, user_id: str) -> int:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.created_at >= today,
            Application.status != ApplicationStatus.pending,
        )
        .count()
    )


def analyze_new_jobs(db: Session, profile: Profile) -> int:
    agent = AnalysisAgent(db)
    jobs = db.query(Job).filter(Job.analyzed.is_(False)).limit(200).all()
    for job in jobs:
        agent.run(job, profile)
    return len(jobs)


def process_user_applications(db: Session, user: User, limit: int = 10) -> dict:
    """Analyze, then for high-scoring jobs build resume+cover and apply (respecting limits)."""
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if not profile:
        return {"error": "no_profile"}
    if user.automation_paused:
        return {"paused": True}

    analyze_new_jobs(db, profile)

    threshold = settings.match_threshold
    cap = settings.max_applications_per_day - _applied_today(db, user.id)
    if cap <= 0:
        return {"capped": True}

    candidates = (
        db.query(Job)
        .filter(Job.analyzed.is_(True), Job.match_score >= threshold)
        .order_by(Job.match_score.desc())
        .limit(limit)
        .all()
    )

    resume_agent = ResumeAgent(db)
    cover_agent = CoverLetterAgent(db)
    app_agent = ApplicationAgent(db)
    created = 0

    for job in candidates:
        if created >= cap:
            break
        if _blacklisted(db, job.company):
            continue
        # already have an application for this job?
        if (
            db.query(Application)
            .filter(Application.user_id == user.id, Application.job_id == job.id)
            .count()
        ):
            continue

        variant = _pick_variant(db, user.id)
        resume = resume_agent.run(job, profile, variant=variant)
        cover = cover_agent.run(job, profile)
        application = Application(
            user_id=user.id,
            job_id=job.id,
            resume_id=resume.id,
            cover_letter_id=cover.id,
            status=ApplicationStatus.pending,
        )
        db.add(application)
        db.commit()
        resume.sends += 1
        db.commit()
        app_agent.run(application, auto_submit=True)
        created += 1

    return {"created": created, "threshold": threshold}


def _pick_variant(db: Session, user_id: str) -> str:
    """A/B/C bucket — rotate so each variant gathers data."""
    from app.db.models import Resume

    counts = {
        v: db.query(Resume).filter(Resume.user_id == user_id, Resume.variant == v).count()
        for v in ("A", "B", "C")
    }
    return min(counts, key=counts.get)


def detect_responses_and_prep(db: Session) -> int:
    """If an application moved to interview, ensure a prep packet exists."""
    from app.agents.interview import InterviewAgent

    agent = InterviewAgent(db)
    apps = (
        db.query(Application)
        .filter(Application.status == ApplicationStatus.interview)
        .all()
    )
    made = 0
    for app in apps:
        if not app.interviews:
            agent.run(app)
            made += 1
    return made


def cleanup_stale(db: Session, days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = db.query(Job).filter(Job.created_at < cutoff, Job.analyzed.is_(False)).delete()
    db.commit()
    return stale
