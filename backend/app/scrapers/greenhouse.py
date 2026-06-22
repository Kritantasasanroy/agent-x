"""Greenhouse job-board connector — public JSON API, automation-friendly.

Greenhouse exposes every customer's board at:
    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

`board_token` is the company slug in their careers URL (e.g. boards.greenhouse.io/<token>).
Configure the boards you want via the GREENHOUSE_BOARDS env var (comma-separated). No auth
needed to read. These boards usually allow application without a CAPTCHA, which is why they
are the best targets for autonomous applying.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.greenhouse")
_TAG = re.compile(r"<[^>]+>")
_REMOTE = re.compile(r"\bremote\b", re.I)
_API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def _unescape(html: str) -> str:
    import html as _h

    return _TAG.sub("", _h.unescape(html or "")).strip()


class GreenhouseScraper(Scraper):
    source = "greenhouse"

    def __init__(self, boards: list[str] | None = None):
        self.boards = boards if boards is not None else settings.greenhouse_boards_list()

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        for board in self.boards:
            try:
                resp = httpx.get(
                    _API.format(board=board),
                    headers={"User-Agent": "JobHunterAI/0.1"},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                log.warning("greenhouse_fetch_failed", board=board, error=str(exc))
                continue
            for j in data.get("jobs", []):
                loc = (j.get("location") or {}).get("name", "")
                desc = _unescape(j.get("content", ""))
                remote = bool(_REMOTE.search(f"{loc} {desc[:400]}"))
                jobs.append(
                    RawJob(
                        source=self.source,
                        external_id=str(j.get("id")),
                        title=j.get("title", ""),
                        company=board,
                        location=loc,
                        remote=remote,
                        description=desc[:6000],
                        apply_url=j.get("absolute_url", ""),
                        raw={"board": board, "gh_id": j.get("id")},
                    )
                )
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
        log.info("greenhouse_fetched", count=len(jobs), boards=len(self.boards))
        return jobs
