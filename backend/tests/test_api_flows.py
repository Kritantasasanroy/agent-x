"""End-to-end API: admin RBAC, company rules, secrets, documents, exports."""

from __future__ import annotations

from app.core.security import create_access_token
from app.db.models import Application, ApplicationStatus, User


def test_admin_pause_resume(auth_client):
    assert auth_client.post("/api/admin/pause").json()["paused"] is True
    assert auth_client.post("/api/admin/resume").json()["paused"] is False


def test_admin_company_rules_crud(auth_client):
    r = auth_client.post("/api/admin/company-rules", json={"company": "EvilCorp", "kind": "blacklist"})
    assert r.status_code == 200
    rules = auth_client.get("/api/admin/company-rules").json()
    assert any(x["company"] == "EvilCorp" for x in rules)
    assert auth_client.delete("/api/admin/company-rules/EvilCorp").status_code == 200


def test_admin_store_encrypted_secret(auth_client):
    r = auth_client.post(
        "/api/admin/secrets",
        json={"key": "OPENAI_API_KEY", "value": "sk-secret", "encrypted": True},
    )
    assert r.status_code == 200
    assert r.json()["encrypted"] is True


def test_admin_audit_logs(auth_client):
    r = auth_client.get("/api/admin/audit-logs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_requires_admin_role(client, db, make_user):
    user, _ = make_user(db, "normaluser@test.com", admin=False)
    token = create_access_token(user.id, {"role": "user"})
    r = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_jobs_list_with_auth(auth_client, db, make_job):
    make_job(db, ext="apiJob1")
    r = auth_client.get("/api/jobs?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_resume_generate_list_download(auth_client, db, make_job):
    auth_client.put("/api/profile", json={"skills": ["python", "fastapi"], "master_resume": "Engineer with Python"})
    job = make_job(db, ext="apiRes1")
    gen = auth_client.post(f"/api/resumes/generate?job_id={job.id}&variant=A")
    assert gen.status_code == 200
    rid = gen.json()["id"]
    listing = auth_client.get("/api/resumes").json()
    assert any(x["id"] == rid for x in listing)
    dl = auth_client.get(f"/api/resumes/{rid}/download?fmt=pdf")
    assert dl.status_code == 200


def test_cover_letter_generate(auth_client, db, make_job):
    auth_client.put("/api/profile", json={"skills": ["python"], "master_resume": "Engineer"})
    job = make_job(db, ext="apiCov1")
    gen = auth_client.post(f"/api/cover-letters/generate?job_id={job.id}")
    assert gen.status_code == 200
    assert gen.json()["content"]


def test_application_status_update(auth_client, db, make_job):
    user = db.query(User).filter(User.email == "admin@test.com").one()
    job = make_job(db, ext="apiApp1")
    application = Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.pending)
    db.add(application)
    db.commit()
    r = auth_client.patch(f"/api/applications/{application.id}/status?status=applied")
    assert r.status_code == 200
    assert r.json()["status"] == "applied"


def test_analytics_export_csv(auth_client):
    r = auth_client.get("/api/analytics/export?fmt=csv")
    assert r.status_code == 200


def test_analytics_recommendations(auth_client):
    r = auth_client.get("/api/analytics/recommendations")
    assert r.status_code == 200
    assert "recommendations" in r.json()


def test_apply_button_works_without_redis(auth_client, db, make_job, monkeypatch):
    # the on-demand Apply must NOT require a Celery broker (regression: was 500 locally)
    monkeypatch.setattr("app.tasks.application_tasks.apply_to_job", lambda *a, **k: None)
    job = make_job(db, ext="btnApply1")
    r = auth_client.post("/api/applications", json={"job_id": job.id, "auto_submit": True})
    assert r.status_code == 200
    assert r.json()["status"] == "processing"


def test_apply_button_404_for_unknown_job(auth_client):
    r = auth_client.post("/api/applications", json={"job_id": "does-not-exist", "auto_submit": True})
    assert r.status_code == 404
