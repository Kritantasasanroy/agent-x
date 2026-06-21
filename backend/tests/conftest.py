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
