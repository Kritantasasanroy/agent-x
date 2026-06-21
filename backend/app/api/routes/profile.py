"""User profile (master resume + preferences)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Profile, User
from app.db.session import get_db
from app.schemas.schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("", response_model=ProfileOut)
def update_profile(
    payload: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
