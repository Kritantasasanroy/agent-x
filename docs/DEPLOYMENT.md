# Deployment Guide

Three supported targets: local Docker, a VPS/Ubuntu server, and Hugging Face Spaces.

## 0. Prerequisites

- Generate secrets:
  ```bash
  python -c "import secrets;print('JWT_SECRET='+secrets.token_urlsafe(48))"
  python -c "from cryptography.fernet import Fernet;print('ENCRYPTION_KEY='+Fernet.generate_key().decode())"
  ```
- Set at least one LLM provider key (`LLM_PROVIDER` + matching `*_API_KEY`). Without a key
  the system still runs but uses a degraded offline text fallback.

## 1. Local / single host (Docker Compose)

```bash
cp .env.example .env        # fill JWT_SECRET, ENCRYPTION_KEY, an LLM key
docker compose up --build -d
docker compose exec api python -m app.cli create-user \
  --email you@example.com --password 'StrongPass123' --admin
```

| Service | URL |
|---------|-----|
| API + Swagger | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |
| Flower (Celery) | http://localhost:5555 |
| Metrics | http://localhost:8000/metrics |

Services: `db` (Postgres), `redis`, `api`, `worker`, `beat`, `flower`, `web`.

## 2. VPS / Ubuntu server

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
git clone https://github.com/Kritantasasanroy/agent-x.git && cd agent-x
cp .env.example .env && nano .env       # set secrets + ENVIRONMENT=production + DEBUG=false
docker compose up --build -d
```

Put Nginx/Caddy in front for TLS. Example Caddyfile:

```
api.example.com { reverse_proxy localhost:8000 }
app.example.com { reverse_proxy localhost:3000 }
```

Set `NEXT_PUBLIC_API_BASE_URL=https://api.example.com` and `CORS_ORIGINS` accordingly,
then rebuild `web`.

### Database migrations (production)

```bash
docker compose exec api alembic upgrade head
# create a new migration after model changes:
docker compose exec api alembic revision --autogenerate -m "describe change"
```

## 3. Hugging Face Spaces

The root `Dockerfile` builds a single container (Redis + worker + beat + API on :7860).
See [deploy/README_HF_SPACE.md](../deploy/README_HF_SPACE.md). Summary:

1. Create a **Docker** Space, push this repo.
2. Add secrets: `JWT_SECRET`, `ENCRYPTION_KEY`, `LLM_PROVIDER`, `*_API_KEY`,
   `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
3. Open `https://<space>.hf.space/docs`.

Spaces storage is ephemeral — use managed Postgres (`DATABASE_URL`) for persistence.
Deploy the frontend separately (Vercel or a Node Space) pointing at the Space API URL.

## 4. Scaling notes

- Run multiple `worker` replicas; Celery shares the Redis broker.
- Move Chroma to a dedicated volume or swap for a hosted vector DB.
- Playwright/Chromium is memory-hungry — give the `worker` container ≥2 GB and isolate
  application-submission tasks on their own queue if volume grows.
