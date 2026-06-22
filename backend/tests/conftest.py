"""Pytest fixtures: isolated sqlite DB + FastAPI TestClient."""

from __future__ import annotations

import os
import tempfile

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret")
os.environ.setdefault("LLM_PROVIDER", "ollama")  # forces offline fallback in tests

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    from app.db.session import session as _session

    s = _session()
    try:
        yield s
    finally:
        s.close()


class FakeLLM:
    """Deterministic stand-in so agent tests never touch the network."""

    def chat(self, system: str, user: str, **kw) -> str:
        return "PROFILE SUMMARY\n\nSKILLS\nPython, FastAPI\n\nEXPERIENCE\n- Engineer"

    def json(self, system: str, user: str, **kw) -> dict:
        return {}


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def make_user():
    from app.core.security import hash_password
    from app.db.models import Profile, Role, User

    def _make(db, email, admin=False, paused=False, skills=None):
        user = User(
            email=email,
            hashed_password=hash_password("pw"),
            full_name="Test User",
            role=Role.admin if admin else Role.user,
            automation_paused=paused,
        )
        db.add(user)
        db.flush()
        profile = Profile(
            user_id=user.id,
            skills=skills if skills is not None else ["python", "fastapi", "docker"],
            years_experience=5,
            master_resume="Senior engineer experienced with Python and FastAPI.",
            preferred_locations=["Remote"],
            min_salary=50000,
        )
        db.add(profile)
        db.commit()
        return user, profile

    return _make


@pytest.fixture
def make_job():
    from app.db.models import Job

    def _make(db, source="remoteok", company="Acme", title="Senior Python Engineer",
              score=90.0, analyzed=True, remote=True, raw=None, ext="1",
              apply_url="https://example.com/apply"):
        job = Job(
            source=source, external_id=ext, fingerprint=f"{source}-{ext}-{company}",
            title=title, company=company, location="Remote", remote=remote,
            description="Python FastAPI Docker, 3+ years experience required.",
            analyzed=analyzed, match_score=score, apply_url=apply_url, raw=raw or {},
        )
        db.add(job)
        db.commit()
        return job

    return _make


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    email = "admin@test.com"
    client.post("/api/auth/register", json={"email": email, "password": "password123", "is_admin": True})
    token = client.post(
        "/api/auth/login", data={"username": email, "password": "password123"}
    ).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
