def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_login_me(client):
    email = "user1@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 200
    r = client.post("/api/auth/login", data={"username": email, "password": "password123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_profile_update(auth_client):
    r = auth_client.put(
        "/api/profile",
        json={"skills": ["Python", "FastAPI"], "preferred_roles": ["Backend Engineer"]},
    )
    assert r.status_code == 200
    assert "Python" in r.json()["skills"]


def test_jobs_requires_auth(client):
    assert client.get("/api/jobs").status_code == 401


def test_analytics_empty(auth_client):
    r = auth_client.get("/api/analytics")
    assert r.status_code == 200
    assert r.json()["total_applications"] == 0
