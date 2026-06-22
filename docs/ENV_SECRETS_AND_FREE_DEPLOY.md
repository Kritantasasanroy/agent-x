# Env, Secrets & Free 24/7 Deploy — the complete reference

Two parts:
1. **Every environment variable / secret** — what it does, whether it's required, where to get it.
2. **Free ways to run it 24/7** with your PC off, ranked, with step-by-step.

---

## Part 1 — Environment variables & secrets

Legend: **Req** = required for the app to work · **Apply** = needed for real auto-applying ·
**Mail** = needed to actually send recruiter emails · **Opt** = optional / nice-to-have.

| Variable | Tier | What it does | Where to get it / how to set |
|----------|------|--------------|------------------------------|
| `JWT_SECRET` | **Req** | Signs login tokens | Any long random string. Generate: `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `ENCRYPTION_KEY` | **Req** | Encrypts stored secrets (Fernet) | `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` |
| `DATABASE_URL` | **Req** | Where data lives | Local: `sqlite+pysqlite:///./jobhunter.db`. Cloud: a Neon/Supabase Postgres URL as `postgresql+psycopg://USER:PASS@HOST/DB` |
| `LLM_PROVIDER` | **Req** | Which AI writes resumes/letters | One of `anthropic` / `openai` / `gemini` / `ollama`. Without a key it still runs on a basic offline fallback |
| `ANTHROPIC_API_KEY` | Apply/quality | Best resume/letter quality | console.anthropic.com → API keys. (Or use OpenAI/Gemini instead) |
| `ANTHROPIC_MODEL` | Opt | Model name | Default `claude-opus-4-8` (or a cheaper one to save money) |
| `OPENAI_API_KEY` | Opt | Alt LLM | platform.openai.com → API keys |
| `GEMINI_API_KEY` | Opt | Alt LLM (has a free quota) | aistudio.google.com → Get API key |
| `OLLAMA_BASE_URL` | Opt | Local free LLM | Install Ollama, `ollama serve`; default `http://localhost:11434` |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Opt* | Real-time scheduler queue | Only for the always-on Celery mode. Free hosted: **Upstash** Redis URL. *Not needed for the GitHub-Actions free path.* |
| `MATCH_THRESHOLD` | Opt | Min score to auto-apply (0–100) | Default `75`. Raise for stricter, lower for more volume |
| `MAX_APPLICATIONS_PER_DAY` | Opt | Daily safety cap | Default `50` |
| `ENABLE_REAL_APPLY` | **Apply** | Master switch for real submissions | `false` by default (dry-run → needs_review). Set `true` only after you've reviewed output |
| `ENABLE_REMOTEOK` / `ENABLE_WEWORKREMOTELY` / `ENABLE_YCOMBINATOR` | Opt | Public job sources | `true` by default; no keys needed |
| `ENABLE_GREENHOUSE` / `ENABLE_LEVER` / `ENABLE_ASHBY` | Opt | Company ATS boards (best auto-apply) | `true`. Then set the slug lists below |
| `GREENHOUSE_BOARDS` | Opt | Which Greenhouse companies | Comma list of slugs from `boards.greenhouse.io/<slug>`, e.g. `stripe,gitlab,airbnb` |
| `LEVER_COMPANIES` | Opt | Which Lever companies | Slugs from `jobs.lever.co/<slug>`, e.g. `leverdemo` |
| `ASHBY_ORGS` | Opt | Which Ashby companies | Slugs from `jobs.ashbyhq.com/<slug>`, e.g. `openai,posthog,linear,ramp` |
| `ENABLE_LINKEDIN/INDEED/GLASSDOOR/WELLFOUND/NAUKRI/FOUNDIT` | Off | ToS-restricted sources | Stay `false`. Only wire via their official API/feed with your own access |
| `SMTP_HOST` | Mail | Outgoing mail server | Gmail: `smtp.gmail.com`. Or SES/Resend/Postmark host |
| `SMTP_PORT` | Mail | Mail port | `587` |
| `SMTP_USER` | Mail | Mailbox login | Your email address |
| `SMTP_PASSWORD` | Mail | Mailbox password | Gmail: an **App Password** (Google Account → Security → 2-Step → App passwords). Not your normal password |
| `SMTP_FROM` | Mail | "From" address | Your email address |
| `TELEGRAM_BOT_TOKEN` | Opt | Instant CAPTCHA/needs-review alerts to your phone | Message **@BotFather** → `/newbot` → copy token |
| `TELEGRAM_CHAT_ID` | Opt | Where to send those alerts | Message **@userinfobot** → it replies with your numeric id |
| `NOTIFY_EMAIL` | Opt | Fallback alert channel | Any inbox you check (used if Telegram unset) |
| `NEXT_PUBLIC_API_BASE_URL` | **Req (UI)** | Tells the UI where the API is | Local `http://localhost:8000`; cloud = your API's public URL |

> **Minimum to run:** `JWT_SECRET`, `ENCRYPTION_KEY`, `DATABASE_URL`, `LLM_PROVIDER` (+ one LLM key for good output).
> **To actually apply for real:** add `ENABLE_REAL_APPLY=true` (after review).
> **To send recruiter mail:** add the five `SMTP_*` vars.
> **To be pinged for CAPTCHAs:** add the two `TELEGRAM_*` vars.

### Where secrets go in each environment
- **Local:** the `.env` file in the project root.
- **GitHub Actions (free autopilot):** repo → Settings → Secrets and variables → Actions → *New repository secret* (one per variable).
- **Oracle/VPS:** the `.env` file next to `docker-compose.yml`.
- **Hugging Face Space:** Space → Settings → *Variables and secrets*.

---

## Part 2 — Free ways to run it 24/7 (PC off)

Your question: *"will UptimeRobot keep the server awake?"* — **Partly.** UptimeRobot pings a URL
every 5 min, which keeps a sleeping **web** service (Render/HF) awake. But it does **not** run
background jobs — it can't make the apply-loop fire. For autonomous applying you need either a
**scheduler** (GitHub Actions) or an **always-on box** (Oracle). Below, ranked for *free + hands-off*.

### 🥇 Option A — GitHub Actions cron + Neon Postgres  (truly free, no server)
This is the best "no PC, no server, $0" path. GitHub runs the `autopilot` loop on a timer; your
data lives in a free cloud Postgres. **No Redis, no always-on host needed.**

1. **Database:** create a free **Neon** project (neon.tech) → copy the connection string. Convert
   the prefix to `postgresql+psycopg://...`. That's your `DATABASE_URL`.
2. **Push the repo** to GitHub (already done: `Kritantasasanroy/agent-x`).
3. **Add secrets** (repo → Settings → Secrets → Actions): `DATABASE_URL`, `JWT_SECRET`,
   `ENCRYPTION_KEY`, `LLM_PROVIDER`, an LLM key, and optionally `ENABLE_REAL_APPLY=true`,
   `GREENHOUSE_BOARDS`, `LEVER_COMPANIES`, `ASHBY_ORGS`, the `SMTP_*` and `TELEGRAM_*` vars.
4. The workflow is already in the repo: **`.github/workflows/autopilot.yml`** (runs every 6h, and
   you can hit "Run workflow" any time). It calls `python -m app.cli autopilot`.
5. **First-time setup of your account:** run `init-db` + `create-user` once (locally pointed at the
   Neon URL, or via a one-off "Run workflow"). Then fill your Profile.
- ✅ Free forever on a public repo (unlimited Actions minutes). ✅ Survives your PC being off.
- ⚠️ Not real-time — it's batch (every N hours). ⚠️ Scheduled workflows auto-disable after ~60
  days with **no repo activity** — one commit/month (or any run) keeps it alive.
- ⚠️ The heavy browser-robot path (Playwright) isn't ideal in Actions; this path shines for the
  **API-based boards** (Greenhouse/Lever/Ashby) + discovery + document generation + outreach.

**Want the dashboard too?** Host the UI free on **Vercel** and the API free on a sleepy host
(below) — but you don't strictly need the API running for autopilot to work.

### 🥈 Option B — Oracle Cloud "Always Free" VM  (real always-on box, full features)
A genuinely free Linux server that never sleeps — runs the *entire* stack (Postgres + Redis +
API + worker + **beat scheduler** + Playwright browser) via `docker compose`, in real time.

- As of **June 15, 2026** the Always-Free ARM (Ampere A1) limit is **2 OCPU / 12 GB RAM / 200 GB**
  — still free forever, and still plenty for this app.
1. Create an Oracle Cloud account (card for identity check; the A1 stays free).
2. Launch an **Ampere A1** VM (Ubuntu, 2 OCPU/12 GB), open ports 22/80/443/3000/8000.
3. `sudo apt install docker.io docker-compose-plugin`, clone the repo, create `.env`.
4. `docker compose up -d` → then `docker compose exec api python -m app.cli create-user ... --admin`.
5. (Optional) point a free domain + Caddy/nginx for HTTPS.
- ✅ Real-time scheduler, full Playwright auto-apply, persistent data, $0.
- ⚠️ Sign-up/capacity can be fiddly; ARM occasionally "out of capacity" (retry/region-hop).
  ⚠️ Idle free VMs can be reclaimed — the app's own activity keeps it alive.

### 🥉 Option C — Hugging Face Space (UI/API) + UptimeRobot + Neon  (for the dashboard)
Good for showing the **dashboard** online; pair with Option A for the actual loop.
1. Deploy the repo's root `Dockerfile` as a **Docker Space**.
2. Set `DATABASE_URL` (Neon) + secrets in Space settings (so data persists — HF disk is **ephemeral**).
3. Add an **UptimeRobot** monitor hitting `/health` every 5 min → resets the 48h sleep timer.
- ✅ Free public dashboard. ⚠️ HF free **sleeps after 48h** and storage is **ephemeral** (use the
  external DB; store files in S3/R2 if you need them to survive). ⚠️ UptimeRobot keeps it **awake**
  but does **not** run the apply loop — that's still Option A or B's job.

### ❌ Not recommended free: Render
Render's free web services sleep after 15 min (UptimeRobot can wake them), but **free background
workers don't run** and **free Postgres expires after 30 days** — so it can't host the autonomous
loop or your data long-term without paying.

---

## Recommended combo for "free, autonomous, applies without me"

- **Now / simplest:** **Option A** (GitHub Actions autopilot + Neon). Zero servers, zero cost,
  applies on a schedule. Add `TELEGRAM_*` so it taps your phone if a CAPTCHA appears.
- **When you want real-time + full browser apply:** move to **Option B** (Oracle Always Free).
- Keep `ENABLE_REAL_APPLY=false` until you've eyeballed a few generated resumes/answers, then flip it.

## Sources
- [Oracle Always Free resources (official)](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) · [2026 A1 limit change](https://space-node.net/blog/oracle-vps-free-tier-review-2026)
- [Render free tier 2026 (sleep / workers / 30-day DB)](https://deploybase.app/blog/render-free-tier-complete-guide-2026)
- [Hugging Face Spaces sleep + ephemeral storage](https://huggingface.co/docs/hub/en/spaces-overview)
