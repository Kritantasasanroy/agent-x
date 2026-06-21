"""Resumes + cover letters: list, get, generate, download files."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.agents.cover_letter import CoverLetterAgent
from app.agents.resume import ResumeAgent
from app.api.deps import get_current_user
from app.db.models import CoverLetter, Job, Profile, Resume, User
from app.db.session import get_db
from app.schemas.schemas import CoverLetterOut, ResumeOut

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/resumes", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).all()
    )


@router.post("/resumes/generate", response_model=ResumeOut)
def generate_resume(
    job_id: str, variant: str = "A", db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    job = db.get(Job, job_id)
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job or profile not found")
    return ResumeAgent(db).run(job, profile, variant=variant)


@router.get("/resumes/{resume_id}/download")
def download_resume(
    resume_id: str, fmt: str = "pdf", db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    path = resume.pdf_path if fmt == "pdf" else resume.docx_path
    if not path:
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(path, filename=f"resume_{resume_id}.{fmt}")


@router.get("/cover-letters", response_model=list[CoverLetterOut])
def list_cover_letters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(CoverLetter)
        .filter(CoverLetter.user_id == user.id)
        .order_by(CoverLetter.created_at.desc())
        .all()
    )


@router.post("/cover-letters/generate", response_model=CoverLetterOut)
def generate_cover(
    job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    job = db.get(Job, job_id)
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job or profile not found")
    return CoverLetterAgent(db).run(job, profile)


@router.get("/cover-letters/{cover_id}/download")
def download_cover(
    cover_id: str, fmt: str = "pdf", db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    cover = db.get(CoverLetter, cover_id)
    if not cover or cover.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    path = cover.pdf_path if fmt == "pdf" else cover.docx_path
    if not path:
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(path, filename=f"cover_{cover_id}.{fmt}")
