# API Reference

Base URL: `http://localhost:8000`. Interactive docs: `/docs` (Swagger) and `/redoc`.
All `/api/*` routes except auth require a `Authorization: Bearer <token>` header.

## Auth
| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/api/auth/register` | `{email, password, full_name?, is_admin?}` | First user becomes admin |
| POST | `/api/auth/login` | form: `username`, `password` | Returns `{access_token}` |
| GET | `/api/auth/me` | — | Current user |

## Profile
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/profile` | Get (auto-creates if missing) |
| PUT | `/api/profile` | Update master resume + preferences |

## Jobs
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/jobs` | Query: `min_score, company, remote, source, limit, offset` |
| GET | `/api/jobs/{id}` | One job |
| POST | `/api/jobs/discover` | Queue a discovery run |

## Applications
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/applications` | Query: `status` |
| POST | `/api/applications` | `{job_id, auto_submit}` — queues apply |
| PATCH | `/api/applications/{id}/status?status=` | Update pipeline status |

## Documents
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/resumes` | List tailored resumes |
| POST | `/api/resumes/generate?job_id=&variant=` | Generate (A/B/C) |
| GET | `/api/resumes/{id}/download?fmt=pdf\|docx` | Download |
| GET | `/api/cover-letters` | List |
| POST | `/api/cover-letters/generate?job_id=` | Generate |
| GET | `/api/cover-letters/{id}/download?fmt=pdf\|docx` | Download |

## Outreach
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/recruiters` | List |
| POST | `/api/recruiters` | Add recruiter |
| POST | `/api/recruiters/{id}/outreach?job_id=` | Start sequence (initial + 7d + 14d) |
| GET | `/api/messages` | List outreach messages |
| POST | `/api/messages/{id}/response?body=&sentiment=` | Record a reply |

## Analytics
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/analytics` | Dashboard metrics |
| GET | `/api/analytics/recommendations` | Learning agent output |
| GET | `/api/analytics/export?fmt=csv\|excel\|pdf` | Export applications |

## Admin (admin role)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/admin/config` | `{automation_paused?, match_threshold?, max_applications_per_day?}` |
| POST | `/api/admin/pause` / `/api/admin/resume` | Stop/start all automation |
| GET/POST | `/api/admin/company-rules` | List / add black/whitelist |
| DELETE | `/api/admin/company-rules/{company}` | Remove rule |
| GET | `/api/admin/audit-logs` | Recent audit entries |
| POST | `/api/admin/secrets` | Store an encrypted secret |

## Ops
| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Liveness |
| GET | `/metrics` | Prometheus metrics |

### Example

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -d 'username=you@example.com&password=StrongPass123' | jq -r .access_token)

curl -s localhost:8000/api/jobs?min_score=75 -H "Authorization: Bearer $TOKEN" | jq
```
