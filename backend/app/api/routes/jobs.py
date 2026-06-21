"""Jobs: list/filter, get one, trigger discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Job, User
from app.db.session import get_db
from app.schemas.schemas import JobOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    min_score: float | None = None,
    company: str | None = None,
    remote: bool | None = None,
    source: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Job]:
    q = db.query(Job)
    if min_score is not None:
        q = q.filter(Job.match_score >= min_score)
    if company:
        q = q.filter(Job.company.ilike(f"%{company}%"))
    if remote is not None:
        q = q.filter(Job.remote.is_(remote))
    if source:
        q = q.filter(Job.source == source)
    return q.order_by(Job.match_score.desc(), Job.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/discover")
def trigger_discovery(_: User = Depends(get_current_user)) -> dict:
    from app.tasks.discovery_tasks import run_discovery

    res = run_discovery.delay()
    return {"task_id": res.id, "status": "queued"}
