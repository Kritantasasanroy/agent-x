# JobHunter AI — Setup, Run, Deploy & Roadmap (plain-English master sheet)

This single document answers, in order:

1. What the system does **right now**
2. How **you** run and use it today (it is running on your PC as you read this)
3. What is **finished** vs **stubbed** (honest matrix)
4. The three sensitive requests — **CAPTCHA auto-pass, scraping Indeed/Glassdoor/Wellfound, auto-creating accounts** — straight talk + the safe version I will build
5. Sending e-mails **autonomously**
6. Deploying it so it runs **24/7 in the cloud with your PC off**
7. How to **add a new job source** (Wellfound / Glassdoor / Indeed / company ATS)
8. The realistic **auto-apply** path (Greenhouse / Lever / Ashby adapters)
9. What **I** will finalize next, in priority order
10. Costs & legal reality

---

## 1. What the system does right now

It is a job-search robot with 9 cooperating "agents" and a web dashboard.

| Agent | What it does today |
|-------|--------------------|
| Discovery | Pulls jobs from RemoteOK, WeWorkRemotely, YC every 30 min, de-dupes them |
| Analysis | Scores each job 0–100 against your profile (skills 40, experience 20, location 15, salary 15, remote 10) |
| Resume | Writes a tailored resume (A/B/C variants) per job, exports **PDF + DOCX**. Never invents experience |
| Cover Letter | Writes a tailored cover letter, PDF + DOCX |
| Application | Opens the job page with a browser robot (Playwright), fills what it safely can. If it hits a CAPTCHA or a form it can't safely complete → marks **needs review** (does not guess, does not bypass) |
| Outreach | Sends recruiter e-mails: first mail + follow-up at 7 days + 14 days, unless they reply |
| Tracking | Records every application's status and history |
| Interview | Builds a prep pack when a reply/interview is detected |
| Learning | Weekly: looks at what worked, recommends best resume variant, keyword and threshold tweaks |

A scheduler (Celery beat) runs these on a clock: discover every 30 min, apply every 15 min, outreach daily, analytics daily, learning weekly.

The dashboard (Next.js) has 14 pages: dashboard, jobs, applications, resumes, cover letters, recruiters, messages, analytics (charts + CSV/Excel/PDF export), profile, settings, admin.

Safety/admin built in: JWT login, admin vs normal user roles, encrypted secrets, audit log, **pause-everything switch**, daily application cap, company blacklist/whitelist.

---

## 2. How you run & use it today (already running)

It is running on your machine right now via the local (no-Docker) path:

- **Dashboard:** http://localhost:3000
- **API docs (Swagger):** http://localhost:8000/docs
- **Login:** `deepak@lemonideas.in` / `ChangeMe123!`  ← change the password after first login
- Database: a local SQLite file `backend/jobhunter.db` (created automatically)
- 103 real jobs already loaded.

### First-use steps
1. Open http://localhost:3000 and log in.
2. Go to **Profile**. Fill it fully — this is the brain food for everything:
   - Paste your **master resume** as plain text.
   - Add **skills**, **preferred roles**, **preferred locations**, **minimum salary**, **years of experience**, LinkedIn/GitHub/portfolio links.
   - Save.
3. Click **Run discovery** on the dashboard. Now scores will be real (no longer 0).
4. Browse **Jobs** (sort by score), open one, click **Apply** to see the tailored resume + cover letter it produces. Review them.
5. Keep automation **paused** at first (Admin → pause). Apply to a few by hand, judge the quality, then unpause.

### To restart it later (after a reboot)
Open two PowerShell windows in `c:\Users\mithu\OneDrive\Desktop\agent-x`:

```powershell
# window 1 — backend
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# window 2 — frontend
cd frontend
npm run dev
```

Note: in this local mode there is **no Redis/Celery**, so the timed automation (every-15-min apply etc.) does **not** run — you trigger actions by clicking. Full automation needs either Docker (next section) or cloud (section 6).

### Run the full stack locally with the clock running (needs Docker Desktop started)
```powershell
# start Docker Desktop first, then:
cp .env.example .env   # edit secrets + one LLM key
docker compose up --build
docker compose exec api python -m app.cli create-user --email you@x.com --password 'StrongPass123' --admin
```
That brings up Postgres + Redis + API + worker + beat (scheduler) + web together, so the timed automation actually fires.

---

## 3. Finished vs stubbed — honest matrix

| Capability | State | Note |
|-----------|-------|------|
| Backend API, auth, roles, DB, encryption, audit | ✅ Working, tested (13/13) | |
| Dashboard UI (14 pages) | ✅ Working, builds clean | |
| Scoring engine | ✅ Working | deterministic, no LLM needed |
| Resume / cover letter generation + PDF/DOCX | ✅ Working | uses LLM if key set, else a basic fallback |
| RemoteOK / WeWorkRemotely sources | ✅ Working | real data pulled |
| **YC source** | ⚠️ **Buggy** | currently pulls Hacker News *comments*, not jobs — I will fix or replace it |
| Scheduler (Celery beat) | ✅ Code complete | only runs when Redis is up (Docker/cloud) |
| Outreach e-mail sequence | ✅ Code complete | sends for real once SMTP is set; until then logs only |
| Application robot (Playwright) | 🟡 Generic only | opens page, fills basic fields, else → needs_review. **No per-site adapters yet** — see §8 |
| Indeed / Glassdoor / Wellfound / LinkedIn / Naukri / Foundit | ⛔ Stubs, OFF | blocked by their ToS — see §4 and §7 |
| Auto account-creation on portals | ❌ Not built | see §4 |
| CAPTCHA auto-pass | ❌ Not built, and I won't | see §4 |
| Cloud 24/7 deploy | 🟡 Image ready | needs external DB + Redis wired — see §6 |
| Vector search / embeddings | 🟡 Fallback active | install `chromadb` + `sentence-transformers` for the real thing |

---

## 4. The three sensitive asks — straight talk

You asked for: (a) auto-fill "I am human" so it never stops, (b) scrape Indeed/Glassdoor/Wellfound, (c) auto-create accounts on company portals. I'll be honest about each, because building the naive version gets your accounts and your real identity **permanently banned**, and some of it I won't build.

### (a) "Auto-fill I-am-human / never stop on CAPTCHA" — I will NOT build a bypass
A CAPTCHA exists for exactly one purpose: to stop bots. There is no clean "tick the box and pass" — modern reCAPTCHA/hCaptcha score your mouse, timing, IP and browser fingerprint.

The only ways people "auto-solve" are:
- **Paid human-solving farms** (2Captcha, Anti-Captcha): a real person abroad solves it for $1–2 per 1000. This **violates the site's terms**, and when detected the site bans the account and often the IP. Used on LinkedIn/Indeed with your real name, you risk losing your actual profile.
- **ML solvers**: unreliable, break weekly, and trip the same fingerprint defenses.

So defeating it is both fragile and a fast path to bans. **What I will build instead — the human-in-the-loop notifier (95% hands-off):** when the robot hits a CAPTCHA or a weird form, it pauses that one application and instantly pings **you** (Telegram bot or e-mail) with a link. You tap it on your phone, solve the CAPTCHA in ~15 seconds, and the robot continues. You stay hands-off for everything else; you only touch the rare hard gate. This is how serious automation is run without getting burned.

### (b) Scraping Indeed / Glassdoor / Wellfound / LinkedIn
Their terms forbid automated scraping, and they enforce it (IP bans, legal notices; LinkedIn has sued scrapers). I won't ship code whose only purpose is to break those terms. **But** the framework has clean plug-in points (§7), and there are **legitimate** ways to get that data:
- **Official / partner APIs & feeds** where they exist (Indeed historically had a Publisher feed; some have partner XML feeds).
- **Licensed aggregators** (e.g., job-data API vendors) whose terms *permit* programmatic use — you pay, you're allowed.
- **Go straight to the source ATS** (next point) — most companies post the same jobs on Greenhouse/Lever/Ashby/Workday, which are far more automation-tolerant and often have public JSON endpoints.

I'll wire any source **you confirm you're authorized to use** (your own API key, a partner feed, or a licensed vendor). That keeps you on the right side of the line and not banned.

### (c) Auto-creating accounts on company career portals
Two realities:
- At **scale**, auto-registering accounts trips anti-fraud and usually violates ToS → bans.
- Many company ATSes (Greenhouse/Lever/Ashby) let you **apply without an account at all** via a public form/endpoint — so account creation is often unnecessary.

What I'll build: for ATS platforms that allow it, **apply directly without an account**; for portals that require login, store **your** credentials encrypted and have the robot log in **as you** (not mass-create throwaways). That's defensible (it's your own job application) and durable.

**Net:** I'll make it as autonomous as it can be *without* the ban-bait pieces. The notifier turns the rare CAPTCHA into a 15-second phone tap instead of a wall.

---

## 5. Sending e-mails autonomously

Already coded (initial + 7-day + 14-day follow-ups). To make it actually send, give it an SMTP account in `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=your-app-password      # Gmail → Security → App passwords (needs 2FA on)
SMTP_FROM=youraddress@gmail.com
```
Better for volume/deliverability: **Amazon SES**, **Resend**, **Postmark**, or **Brave/SendGrid** — they give higher limits and don't flag you as fast.

Rules to not get blacklisted (I'll enforce these in code):
- Only e-mail real, opted-in/relevant recruiter addresses (no scraped spam lists).
- Rate-limit (e.g., ≤ 30–50/day) and randomize timing.
- Always include your name, context, and an opt-out line (CAN-SPAM / GDPR basics).

Finding recruiter e-mails ("e-mail finder") is a separate piece — I'd integrate a **licensed** lookup API (Hunter.io, Apollo) rather than scraping, for the same ban/legal reasons.

---

## 6. Deploy 24/7 in the cloud (your PC off)

"Runs without my PC on" = it has to live on a server. Honest version of the options:

### Reality check on Hugging Face Spaces
- HF **free** Spaces **sleep** after inactivity and have **ephemeral disk** (your DB/files vanish on rebuild). Fine for a demo, not for a 24/7 robot that must remember everything.
- To use HF for real you need: **persistent storage or external DB**, and ideally the paid "always-on" so it doesn't nap.

### Recommended 24/7 architecture (cheap, durable)
Split the stateful bits out to free managed services so the app box can be anything:

```
   [ Hugging Face Space  OR  Railway/Render/Fly.io ]   ← API + Celery worker + beat (the single-container image already exists)
            |                         |
   [ Neon / Supabase Postgres ]   [ Upstash Redis ]     ← free tiers, persistent
            |
   [ Cloudflare R2 / S3 ]                                ← store resumes & screenshots (containers are ephemeral)
```

Concrete steps:
1. **Postgres:** create a free **Neon** (or Supabase) DB → copy its connection string into `DATABASE_URL` (use `postgresql+psycopg://...`).
2. **Redis:** create a free **Upstash** Redis → put its URL in `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
3. **App host:** push the repo; the root `Dockerfile` already runs redis+api+worker+beat in one box for HF — for Railway/Render, run API and worker/beat as two services pointing at the same env.
4. **Secrets:** set `JWT_SECRET`, `ENCRYPTION_KEY`, one LLM key, SMTP vars, `DATABASE_URL`, `REDIS_URL` in the host's secrets panel (never commit them).
5. **File storage:** add S3/R2 keys; I'll switch document/screenshot writes from local disk to the bucket so nothing is lost on restart.
6. **Run DB migrations** once (`alembic upgrade head`) and create your admin user.

### Simplest truly-24/7 (my recommendation): a $4–6/mo VPS
A tiny **Hetzner / DigitalOcean / Vultr** box running `docker compose up -d` gives you Postgres + Redis + API + worker + **beat scheduler** all persistent, always on, no sleep, full Playwright support (the browser robot needs real CPU/RAM that free tiers often don't give). This is the least-fuss path to "set it and forget it."

> Note: the Playwright apply-robot is heavy (a real Chromium). Free serverless tiers often can't run it. A small VPS is the realistic home for the apply worker.

---

## 7. How to add a new job source

Every source is one small file implementing a scraper. The plug-in points:

- `backend/app/scrapers/base.py` — defines `RawJob` (with `fingerprint()` for de-dupe) and the base class.
- `backend/app/scrapers/__init__.py` — `active_scrapers()` registry (reads the `ENABLE_*` flags).
- `backend/app/core/config.py` — the `ENABLE_<SOURCE>` flag.

Skeleton for a new authorized source (e.g., a company's Greenhouse board, which is public JSON):

```python
# backend/app/scrapers/greenhouse.py
import httpx
from .base import BaseScraper, RawJob

class GreenhouseScraper(BaseScraper):
    name = "greenhouse"
    def __init__(self, board: str): self.board = board
    def fetch(self) -> list[RawJob]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs?content=true"
        data = httpx.get(url, timeout=20).json()
        out = []
        for j in data.get("jobs", []):
            out.append(RawJob(
                source=self.name, title=j["title"], company=self.board,
                location=j.get("location", {}).get("name", ""),
                url=j["absolute_url"], description=j.get("content", ""),
            ))
        return out
```
Then add `ENABLE_GREENHOUSE` to config and register it in `__init__.py`. Same shape for Lever (`api.lever.co/v0/postings/<company>?mode=json`) and Ashby — these are public and automation-friendly, which is why they're the smart sources to add first. For ToS-restricted sites, the same file would call **their official API with your key / a licensed feed**, not raw HTML scraping.

---

## 8. The realistic auto-apply path (ATS adapters)

Generic "fill any form on any site" is unreliable — every site differs. The proven approach is **per-ATS adapters**, because most jobs funnel through a handful of systems:

- **Greenhouse**, **Lever**, **Ashby** — often allow application via public form/endpoint, sometimes **no account needed**.
- **Workday**, **Taleo** — login-based, harder, build later.

Each adapter knows that one system's fields (name, email, resume upload, the standard questions) and fills them reliably, with the CAPTCHA-notifier (§4a) as the fallback for the rare gate. This is the high-value thing I'd build next, and it's the version that actually lands applications instead of piling up `needs_review`.

---

## 9. What I will finalize next (priority order)

1. **CAPTCHA/needs-review notifier** (Telegram + e-mail) — turns the only real blocker into a 15-sec phone tap. *Biggest autonomy win.*
2. **Fix/replace the YC source** and add **Greenhouse + Lever + Ashby** scrapers (real, allowed, high-volume).
3. **Greenhouse/Lever apply adapters** — real submitted applications, not dry runs.
4. **Cloud deploy wiring** — external Postgres (Neon) + Redis (Upstash) + S3/R2 for files, so it runs 24/7 with your PC off; plus a one-command VPS compose.
5. **SMTP + safe outreach throttling** live, optional licensed e-mail-finder.
6. Install/enable real **embeddings + ChromaDB** for better matching.
7. Polish: login-as-you credential vault for portals that require accounts.

Tell me the order you want; #1 and #4 together get you "runs in the cloud, only pings me when it truly needs a human."

---

## 10. Costs & legal reality

**Likely monthly cost (lean):**
- VPS (Hetzner CX22 or similar): ~$4–6, **or** free tiers (HF/Railway/Neon/Upstash) = $0 but with sleep/limits.
- LLM API: pay-per-use; with a cheap/local model or careful prompts, a few dollars/month for personal volume. Local Ollama = $0 but needs a beefier box.
- E-mail (SES/Resend): free tier covers personal volume.
- Licensed job/e-mail data APIs (only if you choose them): variable.

**Legal/ban reality (short version):**
- Scraping or auto-applying on sites that forbid it risks IP/account bans and, for big sites, legal letters. Using **your own** credentials for **your own** applications, official APIs, licensed feeds, and automation-friendly ATSes keeps you safe.
- CAPTCHAs are an access control; defeating them is the line I won't cross. The notifier gives you near-full autonomy without it.
- For e-mail: stay within anti-spam law (relevant recipients, identify yourself, allow opt-out, rate-limit).

---

*Generated for Deepak. The app is running locally now — log in, fill your profile, and click around. When you're ready, tell me which roadmap items to build and whether you want the VPS or the HF/managed-services deploy path.*
