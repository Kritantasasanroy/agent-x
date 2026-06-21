# User Guide

## 1. First run

1. Open the dashboard (`http://localhost:3000`) and **Register**. The first account is the
   admin.
2. Go to **Profile** and fill it in — this drives everything:
   - Paste your **master resume** (plain text).
   - Add **skills**, **preferred roles**, **preferred locations**, **min salary**,
     **years of experience**, and your LinkedIn/GitHub/portfolio links.
3. Save.

> The richer your profile, the better the match scores, tailored resumes, and outreach.

## 2. Find jobs

- Click **Run discovery now** on the Dashboard (or it runs automatically every 30 min).
- Jobs are pulled from the enabled sources (RemoteOK, WeWorkRemotely, YC by default),
  deduped, and scored 0–100 against your profile.
- Browse **Jobs**, filter by score/company.

## 3. Apply

- Click **Apply** on a job, or let automation do it: every 15 min the system applies to
  jobs scoring ≥ threshold (default 75), generating a tailored **resume** + **cover letter**
  per application.
- If a site shows a **CAPTCHA** or a form the bot can't safely complete, the application is
  marked **needs review** — you finish it by hand. The bot never solves CAPTCHAs.
- Track progress on **Applications**; move cards through pending → applied → interview →
  offer/rejected.

## 4. Resumes & cover letters

- **Resumes** page lists every tailored version (variants A/B/C) with PDF/DOCX downloads and
  performance counters (sends / responses / interviews).
- **Cover Letters** page shows generated letters with downloads.

## 5. Recruiter outreach

- Add recruiters on the **Recruiters** page, then **Start outreach** to send a personalized
  email plus scheduled follow-ups (7 and 14 days) — unless they reply first.
- Record replies via the API/Messages so follow-ups stop and interview prep can trigger.

## 6. Analytics & learning

- **Analytics** shows applications by status/source, interview/response/offer rates, charts,
  and CSV/Excel/PDF export.
- The **Learning agent** runs weekly and posts recommendations (best resume variant, keyword
  and threshold tweaks).

## 7. Admin controls

- **Pause all** to stop automation instantly.
- Set **match threshold** and **max applications/day**.
- **Blacklist** companies you never want applied to (or **whitelist** to restrict to a set).
- Review the **audit log**.

## 8. Tips

- Start with automation paused, apply to a few jobs manually, and review the generated
  documents before turning automation on.
- Only enable extra job sources you're permitted to use (see Security doc).
