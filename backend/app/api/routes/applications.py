"""Applications: list, get, create (apply), update status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.tracking import TrackingAgent
from app.api.deps import get_current_user
from app.db.models import Application, ApplicationStatus, User
from app.db.session import get_db
from app.schemas.schemas import ApplicationCreate, ApplicationOut

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Application]:
    q = db.query(Application).filter(Application.user_id == user.id)
    if status:
        q = q.filter(Application.status == status)
    return q.order_by(Application.created_at.desc()).all()


@router.post("", response_model=dict)
def create_application(
    payload: ApplicationCreate,
    user: User = Depends(get_current_user),
) -> dict:
    from app.tasks.application_tasks import apply_to_job

    res = apply_to_job.delay(user.id, payload.job_id, payload.auto_submit)
    return {"task_id": res.id, "status": "queued"}


@router.patch("/{app_id}/status", response_model=ApplicationOut)
def update_status(
    app_id: str,
    status: ApplicationStatus,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Application:
    app = db.get(Application, app_id)
    if not app or app.user_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    TrackingAgent(db).set_status(app, status)
    return app
