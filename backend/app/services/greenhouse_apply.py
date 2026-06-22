"""Greenhouse direct application via the public Job Board API.

Greenhouse boards accept applications at:
    POST https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}

as multipart/form-data with at least first_name, last_name, email and a resume file, plus
any board-specific question fields. This is the cleanest, most automation-friendly apply
path (no CAPTCHA on most boards), so we prefer it over the generic browser robot when a job
came from Greenhouse.

Safety: a real POST only happens when settings.enable_real_apply is True. Otherwise we build
and return the payload as a dry run so it can be reviewed/tested without submitting anything.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Job, Profile, Resume

log = get_logger("apply.greenhouse")
_SUBMIT = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"


@dataclass
class ApplyResult:
    submitted: bool
    dry_run: bool
    status_code: int = 0
    reason: str = ""
    fields: dict | None = None


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split()
    if not parts:
        return "Applicant", "Applicant"
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], " ".join(parts[1:])


def build_fields(profile: Profile, job: Job) -> dict:
    """Map a profile to Greenhouse's standard application fields."""
    full_name = profile.user.full_name if profile and profile.user else ""
    first, last = _split_name(full_name)
    return {
        "first_name": first,
        "last_name": last,
        "email": (profile.user.email if profile and profile.user else ""),
        "phone": (profile.phone if profile else ""),
        "location": (profile.location if profile else ""),
        "linkedin_url": (profile.linkedin_url if profile else ""),
        "website": (profile.portfolio_url if profile else ""),
        "github_url": (profile.github_url if profile else ""),
    }


def gh_ids(job: Job) -> tuple[str, str] | None:
    """Recover (board, job_id) from a Greenhouse job row."""
    raw = job.raw or {}
    board = raw.get("board")
    gh_id = raw.get("gh_id") or job.external_id
    if board and gh_id:
        return str(board), str(gh_id)
    return None


def apply(profile: Profile, job: Job, resume: Resume | None) -> ApplyResult:
    ids = gh_ids(job)
    if not ids:
        return ApplyResult(False, dry_run=True, reason="not_a_greenhouse_job")
    board, job_id = ids
    fields = build_fields(profile, job)

    if not settings.enable_real_apply:
        log.info("greenhouse_apply_dry_run", board=board, job_id=job_id)
        return ApplyResult(False, dry_run=True, reason="real_apply_disabled", fields=fields)

    files = {}
    if resume and resume.pdf_path:
        try:
            files["resume"] = ("resume.pdf", open(resume.pdf_path, "rb"), "application/pdf")
        except OSError:
            pass
    try:
        resp = httpx.post(
            _SUBMIT.format(board=board, job_id=job_id),
            data=fields,
            files=files or None,
            timeout=60,
        )
        ok = resp.status_code in (200, 201)
        log.info("greenhouse_apply_posted", board=board, job_id=job_id, status=resp.status_code)
        return ApplyResult(ok, dry_run=False, status_code=resp.status_code,
                           reason="" if ok else resp.text[:200], fields=fields)
    except Exception as exc:  # noqa: BLE001
        log.warning("greenhouse_apply_failed", error=str(exc))
        return ApplyResult(False, dry_run=False, reason=str(exc)[:200], fields=fields)
    finally:
        for f in files.values():
            try:
                f[1].close()
            except Exception:  # noqa: BLE001
                pass
