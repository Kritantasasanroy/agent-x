"""Admin: pause automation, limits, black/whitelist, audit logs, secrets."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.core.security import encrypt
from app.db.models import AuditLog, CompanyRule, Setting, User
from app.db.session import get_db
from app.schemas.schemas import AdminConfig, CompanyRuleIn, SettingIn

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/config")
def update_config(
    payload: AdminConfig, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> dict:
    if payload.automation_paused is not None:
        for user in db.query(User).all():
            user.automation_paused = payload.automation_paused
    if payload.match_threshold is not None:
        settings.match_threshold = payload.match_threshold
    if payload.max_applications_per_day is not None:
        settings.max_applications_per_day = payload.max_applications_per_day
    db.add(AuditLog(actor=admin.email, action="admin_config", meta=payload.model_dump(exclude_none=True)))
    db.commit()
    return {
        "automation_paused": payload.automation_paused,
        "match_threshold": settings.match_threshold,
        "max_applications_per_day": settings.max_applications_per_day,
    }


@router.post("/pause")
def pause_all(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    for user in db.query(User).all():
        user.automation_paused = True
    db.add(AuditLog(actor=admin.email, action="pause_all"))
    db.commit()
    return {"paused": True}


@router.post("/resume")
def resume_all(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    for user in db.query(User).all():
        user.automation_paused = False
    db.add(AuditLog(actor=admin.email, action="resume_all"))
    db.commit()
    return {"paused": False}


@router.get("/company-rules")
def list_rules(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(CompanyRule).all()


@router.post("/company-rules")
def add_rule(
    payload: CompanyRuleIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> dict:
    rule = db.query(CompanyRule).filter(CompanyRule.company.ilike(payload.company)).one_or_none()
    if rule:
        rule.kind = payload.kind
    else:
        db.add(CompanyRule(company=payload.company, kind=payload.kind))
    db.add(AuditLog(actor=admin.email, action="company_rule", target=payload.company, meta={"kind": payload.kind}))
    db.commit()
    return {"company": payload.company, "kind": payload.kind}


@router.delete("/company-rules/{company}")
def delete_rule(company: str, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    db.query(CompanyRule).filter(CompanyRule.company.ilike(company)).delete()
    db.commit()
    return {"deleted": company}


@router.get("/audit-logs")
def audit_logs(limit: int = 200, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.post("/secrets")
def set_secret(
    payload: SettingIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> dict:
    value = encrypt(payload.value) if payload.encrypted else payload.value
    setting = (
        db.query(Setting).filter(Setting.user_id.is_(None), Setting.key == payload.key).one_or_none()
    )
    if not setting:
        setting = Setting(user_id=None, key=payload.key)
        db.add(setting)
    setting.value = value
    setting.encrypted = payload.encrypted
    db.add(AuditLog(actor=admin.email, action="set_secret", target=payload.key))
    db.commit()
    return {"key": payload.key, "encrypted": payload.encrypted}
