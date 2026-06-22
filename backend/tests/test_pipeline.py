"""Pipeline orchestration: pause, profile, blacklist/whitelist, caps, apply creation."""

from __future__ import annotations

from app.agents import pipeline
from app.core.security import hash_password
from app.db.models import Application, ApplicationStatus, CompanyRule, Role, User


def test_paused_user_is_skipped(db, make_user):
    user, _ = make_user(db, "ppause@test.com", paused=True)
    assert pipeline.process_user_applications(db, user) == {"paused": True}


def test_missing_profile_errors(db):
    user = User(email="pnoprof@test.com", hashed_password=hash_password("pw"), role=Role.user)
    db.add(user)
    db.commit()
    assert pipeline.process_user_applications(db, user) == {"error": "no_profile"}


def test_blacklist_then_cleanup(db):
    db.add(CompanyRule(company="BadCorp", kind="blacklist"))
    db.commit()
    try:
        assert pipeline._blacklisted(db, "badcorp") is True   # case-insensitive
        assert pipeline._blacklisted(db, "GoodCorp") is False
    finally:
        db.query(CompanyRule).delete()
        db.commit()


def test_whitelist_restricts_then_cleanup(db):
    db.add(CompanyRule(company="OnlyThis", kind="whitelist"))
    db.commit()
    try:
        assert pipeline._blacklisted(db, "OnlyThis") is False     # whitelisted -> allowed
        assert pipeline._blacklisted(db, "SomethingElse") is True  # not whitelisted -> blocked
    finally:
        db.query(CompanyRule).delete()
        db.commit()


def test_process_creates_applications(db, make_user, make_job, monkeypatch):
    db.query(CompanyRule).delete()
    db.commit()
    # raise threshold so ONLY our two high-score greenhouse jobs qualify (isolates from other tests)
    monkeypatch.setattr(pipeline.settings, "match_threshold", 93)
    user, _ = make_user(db, "pproc@test.com")
    make_job(db, source="greenhouse", company="GhCoA", ext="pp1", raw={"board": "ghcoa", "gh_id": 1}, score=96)
    make_job(db, source="greenhouse", company="GhCoB", ext="pp2", raw={"board": "ghcob", "gh_id": 2}, score=95)

    result = pipeline.process_user_applications(db, user, limit=5)
    assert result.get("created", 0) >= 1

    apps = db.query(Application).filter(Application.user_id == user.id).all()
    assert len(apps) >= 1
    # greenhouse dry-run (real apply disabled) -> needs_review, never silently "applied"
    assert all(a.status == ApplicationStatus.needs_review for a in apps)


def test_pick_variant_rotates(db, make_user):
    from app.db.models import Resume

    user, _ = make_user(db, "pvariant@test.com")
    # with no resumes yet all counts are 0 -> returns the first bucket
    assert pipeline._pick_variant(db, user.id) in ("A", "B", "C")
    db.add(Resume(user_id=user.id, variant="A", sends=0))
    db.add(Resume(user_id=user.id, variant="B", sends=0))
    db.commit()
    # C has the fewest -> should be chosen
    assert pipeline._pick_variant(db, user.id) == "C"
