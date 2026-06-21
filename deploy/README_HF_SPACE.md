---
title: JobHunter AI
emoji: 🦣
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# JobHunter AI — Hugging Face Space

This Space runs the JobHunter AI **backend** (API + Celery worker + beat + Redis) in one
Docker container on port 7860. Open `/docs` for the interactive API, `/health` for health.

## Setup

1. Create a **Docker** Space and push this repo (the root `Dockerfile` is used automatically).
2. In Space **Settings → Variables and secrets**, set at least:
   - `JWT_SECRET` — long random string
   - `ENCRYPTION_KEY` — Fernet key (`python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`)
   - `LLM_PROVIDER` + the matching `*_API_KEY` (e.g. `ANTHROPIC_API_KEY`)
   - `ADMIN_EMAIL` + `ADMIN_PASSWORD` — auto-creates the first admin on boot
3. Deploy. Visit `https://<your-space>.hf.space/docs`.

> Hugging Face Spaces storage is ephemeral unless you attach persistent storage. Use the
> SQLite default for demos; point `DATABASE_URL` at managed Postgres for anything real.

Deploy the **frontend** as a separate static/Node Space (or Vercel) with
`NEXT_PUBLIC_API_BASE_URL` pointing at this Space URL.
