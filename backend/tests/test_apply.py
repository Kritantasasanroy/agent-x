"""Greenhouse apply adapter + Application agent routing (no real submissions)."""

from __future__ import annotations

from types import SimpleNamespace

from app.db.models import Application, ApplicationStatus
from app.services import greenhouse_apply as ga


def test_split_name():
    assert ga._split_name("Deepak Kumar") == ("Deepak", "Kumar")
    assert ga._split_name("Cher") == ("Cher", "Cher")
    assert ga._split_name("") == ("Applicant", "Applicant")
    assert ga._split_name("A B C") == ("A", "B C")


def test_build_fields():
    user = SimpleNamespace(full_name="Deepak Kumar", email="d@x.com")
    profile = SimpleNamespace(
        user=user, phone="123", location="NYC",
        linkedin_url="li", portfolio_url="pf", github_url="gh",
    )
    fields = ga.build_fields(profile, SimpleNamespace())
    assert fields["first_name"] == "Deepak"
    assert fields["last_name"] == "Kumar"
    assert fields["email"] == "d@x.com"
    assert fields["linkedin_url"] == "li"


def test_gh_ids():
    job = SimpleNamespace(raw={"board": "acme", "gh_id": 123}, external_id="123")
    assert ga.gh_ids(job) == ("acme", "123")
    assert ga.gh_ids(SimpleNamespace(raw={}, external_id="x")) is None


def test_apply_is_dry_run_by_default(monkeypatch):
    # enable_real_apply defaults False -> must NOT touch network
    monkeypatch.setattr(ga.httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    user = SimpleNamespace(full_name="A B", email="a@b.com")
    profile = SimpleNamespace(
        user=user, phone="", location="", linkedin_url="", portfolio_url="", github_url=""
    )
    job = SimpleNamespace(raw={"board": "acme", "gh_id": 1}, external_id="1")
    result = ga.apply(profile, job, None)
    assert result.dry_run is True
    assert result.submitted is False
    assert result.fields["email"] == "a@b.com"


def test_application_agent_greenhouse_dry_run(db, fake_llm, make_user, make_job):
    from app.agents.application import ApplicationAgent

    user, _ = make_user(db, "ghapply@test.com")
    job = make_job(db, source="greenhouse", ext="gh1", raw={"board": "acme", "gh_id": 555})
    application = Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.pending)
    db.add(application)
    db.commit()

    ApplicationAgent(db, llm=fake_llm).run(application, auto_submit=True)
    # real apply disabled -> needs_review, never silently "applied"
    assert application.status == ApplicationStatus.needs_review
    assert application.needs_review_reason.startswith("greenhouse_dry_run")
    assert application.answers.get("email") == "ghapply@test.com"
