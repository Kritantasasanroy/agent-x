"""Recruiters + messages + responses."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Message, Recruiter, Response, User
from app.db.session import get_db
from app.schemas.schemas import MessageOut, RecruiterOut

router = APIRouter(prefix="/api", tags=["outreach"])


@router.get("/recruiters", response_model=list[RecruiterOut])
def list_recruiters(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Recruiter).order_by(Recruiter.created_at.desc()).all()


@router.post("/recruiters", response_model=RecruiterOut)
def add_recruiter(
    payload: RecruiterOut, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    recruiter = Recruiter(
        name=payload.name, title=payload.title, company=payload.company,
        email=payload.email, linkedin_url=payload.linkedin_url, source=payload.source,
    )
    db.add(recruiter)
    db.commit()
    db.refresh(recruiter)
    return recruiter


@router.post("/recruiters/{recruiter_id}/outreach")
def start_outreach(
    recruiter_id: str, job_id: str | None = None, user: User = Depends(get_current_user)
):
    from app.tasks.outreach_tasks import start_sequence

    res = start_sequence.delay(user.id, recruiter_id, job_id)
    return {"task_id": res.id, "status": "queued"}


@router.get("/messages", response_model=list[MessageOut])
def list_messages(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Message)
        .filter(Message.user_id == user.id)
        .order_by(Message.created_at.desc())
        .all()
    )


@router.post("/messages/{message_id}/response")
def record_response(
    message_id: str, body: str, sentiment: str = "positive",
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.add(Response(message_id=message_id, body=body, sentiment=sentiment))
    db.commit()
    return {"ok": True}
