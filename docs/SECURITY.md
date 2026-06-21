# Security & Compliance

## Secrets & encryption

- **Passwords** — hashed with bcrypt (`passlib`), never stored in plaintext.
- **API keys / tokens / SMTP creds** — encrypted at rest with Fernet (AES-128-CBC + HMAC)
  via `app.core.security.encrypt/decrypt`. The key comes from `ENCRYPTION_KEY`; if unset it
  is derived from `JWT_SECRET` (set a real `ENCRYPTION_KEY` in production).
- **JWT** — HS256, signed with `JWT_SECRET`, default 60-min expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Secrets are provided via environment / `.env` (gitignored) or the admin secrets endpoint.
  Nothing sensitive is persisted to the frontend/localStorage except the bearer token.

## AuthN / AuthZ (RBAC)

- Two roles: `admin` and `user` (`app.db.models.Role`).
- The first registered user is auto-promoted to `admin`.
- Admin-only routes are gated by `require_admin` (`/api/admin/*`).
- Every user's data is scoped by `user_id` on queries.

## Audit logging

- `AuditLog` records actor, action, target, metadata + timestamp.
- Agents and admin actions write audit entries (discovery runs, applications, status
  changes, config changes, secret writes, pause/resume). View at `/api/admin/audit-logs`.

## Session management

- Stateless JWT bearer tokens. Logout clears the client token. Rotate `JWT_SECRET` to
  invalidate all sessions. Playwright login sessions are stored per-user under
  `storage/playwright/<user>/state.json` (gitignored) for cookie reuse.

## Responsible-automation safeguards

- **CAPTCHAs are never bypassed.** On detection the Application agent stops and flags the
  application `needs_review` for a human (`CAPTCHA_MARKERS` in `agents/application.py`).
- **ToS-restricted sources** (LinkedIn, Indeed, Naukri, Glassdoor, Wellfound, Foundit) ship
  **disabled** as stubs. Enabling them is your responsibility and may breach their Terms.
- **Rate limits**: `MAX_APPLICATIONS_PER_DAY` (default 50) + admin pause switch.
- **No fabrication**: resume/cover agents are prompted to never invent experience.
- Company **black/whitelist** lets you exclude or restrict employers.

## Hardening checklist (production)

- [ ] Strong unique `JWT_SECRET` and `ENCRYPTION_KEY`
- [ ] `ENVIRONMENT=production`, `DEBUG=false`
- [ ] Restrict `CORS_ORIGINS` to your domains (not `*`)
- [ ] TLS in front (Caddy/Nginx)
- [ ] Managed Postgres with backups; Redis not publicly exposed
- [ ] Run containers as non-root; keep base images patched
- [ ] Rotate LLM/SMTP keys; scope them minimally

## Reporting

Found a vulnerability? Open a private security advisory on the GitHub repo rather than a
public issue.
