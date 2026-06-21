# JobHunter AI 🦣

Autonomous AI job-search & application platform. It finds jobs, scores them against your
profile, tailors resumes + cover letters, applies when it can, reaches out to recruiters,
tracks everything, and learns from outcomes — with a human-in-the-loop dashboard.

> ⚠️ **Read before you run.** Scraping/auto-applying on some sites (LinkedIn, Indeed,
> Naukri…) can violate their Terms of Service. Connectors for those sites ship **disabled**
> as plug-in stubs. Only enable what you are allowed to use. The system **never** bypasses
> CAPTCHAs — it pauses and asks a human. You are responsible for how you use this.

## Architecture

Multi-agent system. Agents are independent and talk over a Celery/Redis queue.

| # | Agent | Job |
|---|-------|-----|
| 1 | Discovery | Search job sources, dedupe, store |
| 2 | Analysis | Extract requirements, compute match score 0–100 |
| 3 | Resume | Tailor master resume to a job (PDF + DOCX) |
| 4 | Cover Letter | Personalized 250–400 word letter (PDF + DOCX) |
| 5 | Application | Playwright auto-fill + submit, screenshots, human-review on CAPTCHA |
| 6 | Outreach | Cold email / message sequences to recruiters |
| 7 | Tracking | Status pipeline + dashboard metrics |
| 8 | Interview | Prep packet on positive response |
| 9 | Learning | Analyze outcomes, recommend improvements |

```
Discovery → Analysis → (score≥threshold) → Resume + Cover → Application
                                         ↘ Outreach
   All events → Tracking → Analytics → Learning ↺ (feeds back thresholds/keywords)
```

## Stack

Backend: Python 3.12 · FastAPI · SQLAlchemy · Celery · Redis · PostgreSQL · ChromaDB ·
Sentence-Transformers · Playwright. LLM: OpenAI / Anthropic / Gemini / Ollama (pluggable).
Frontend: Next.js · React · Tailwind. Ops: Docker · Prometheus · structured JSON logs ·
GitHub Actions CI.

## Quick start (local, Docker)

```bash
cp .env.example .env          # fill in at least JWT_SECRET, ENCRYPTION_KEY, one LLM key
docker compose up --build
# API   -> http://localhost:8000/docs
# UI    -> http://localhost:3000
# Flower-> http://localhost:5555
```

Create the first user:

```bash
docker compose exec api python -m app.cli create-user \
  --email you@example.com --password 'change-me' --admin
```

## Quick start (no Docker)

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
# separate shells:
celery -A app.core.celery_app.celery worker -l info -P solo
celery -A app.core.celery_app.celery beat -l info
```

```bash
cd frontend && npm install && npm run dev
```

## Docs

- [Deployment](docs/DEPLOYMENT.md) — Docker, VPS/Ubuntu, Hugging Face Spaces
- [Security](docs/SECURITY.md) — encryption, RBAC, audit logs, secrets
- [API](docs/API.md) — endpoint reference (also live at `/docs`)
- [User guide](docs/USER_GUIDE.md)

## Status

This is a **production-shaped foundation**, not a finished SaaS. Core (auth, DB, agents
orchestration, scoring, doc generation, dashboard, Docker, CI) is real and runs. Site
connectors that touch ToS-restricted platforms and some LLM-heavy flows are clearly marked
stubs you extend. See `// TODO`/`# TODO(stub)` markers.

## License

MIT — see [LICENSE](LICENSE). Use responsibly and legally.
