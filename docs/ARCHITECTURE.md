# Architecture

```
                         ┌────────────────────────────┐
                         │        Next.js UI           │
                         │  (dashboard, jobs, apps…)   │
                         └──────────────┬──────────────┘
                                        │ REST + JWT
                         ┌──────────────▼──────────────┐
                         │          FastAPI            │
                         │  auth · profile · jobs ·    │
                         │  applications · documents · │
                         │  outreach · analytics · admin│
                         └───────┬───────────────┬─────┘
                                 │               │
                   enqueue tasks │               │ read/write
                         ┌───────▼──────┐  ┌─────▼──────┐
                         │  Redis +     │  │ PostgreSQL │
                         │  Celery      │  │ (SQLAlchemy)│
                         │  worker/beat │  └─────┬──────┘
                         └───────┬──────┘        │
        ┌────────────────────────┼───────────────┘
        │            Agents (independent, queue-driven)
        ▼
  Discovery → Analysis → Resume + CoverLetter → Application
        │                                   ╲
        │                                    ╲→ Outreach → (replies) → Interview
        └────────────► Tracking ──► Analytics ──► Learning ↺
                                   (feeds thresholds / keywords / best variant)

  Services: LLM (OpenAI/Anthropic/Gemini/Ollama) · Embeddings (Sentence-Transformers) ·
            Vector store (ChromaDB) · Documents (PDF/DOCX) · Email (SMTP)
  Scrapers: RemoteOK · WeWorkRemotely · YCombinator (+ disabled ToS-restricted stubs)
```

## Layout

```
backend/app
  core/        config, security, logging, metrics, celery_app
  db/          base, session, models
  schemas/     pydantic IO models
  services/    llm, embeddings, vector_store, documents, email
  scrapers/    base + per-source connectors
  agents/      9 agents + pipeline orchestrator
  tasks/       celery tasks (discovery/application/outreach/analytics/learning)
  api/routes/  auth, profile, jobs, applications, documents, outreach, analytics, admin
  main.py      app factory   ·   cli.py  management CLI
frontend/src   Next.js App Router pages + components + api client
deploy/        HF Spaces start script + Space README
docs/          deployment, security, api, user guide, architecture
```

## Scheduler (Celery beat)

| Task | Cadence |
|------|---------|
| Discovery + analysis | every 30 min |
| Application processing | every 15 min |
| Recruiter outreach follow-ups | daily 09:00 UTC |
| Analytics refresh + cleanup | daily 01:00 UTC |
| Learning agent | weekly (Sun 02:00 UTC) |

## Design choices

- **Graceful degradation**: LLM, embeddings, vector store, Playwright and SMTP all have
  offline/no-op fallbacks so the system boots and the pipeline survives missing optional
  infra — useful for CI, demos, and HF Spaces.
- **Deterministic scoring**: match score is computable without an LLM (skills/exp/location/
  salary/remote weights), keeping behavior testable and cheap.
- **Human-in-the-loop**: CAPTCHAs and ambiguous forms route to `needs_review`; admins can
  pause everything and cap daily volume.
```
