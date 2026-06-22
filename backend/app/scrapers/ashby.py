"""Ashby job-board connector — public JSON API.

    https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true

`org` is the slug in jobs.ashbyhq.com/<org>. Configure via ASHBY_ORGS (comma-separated).
No auth needed to read the public board.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.ashby")
_REMOTE = re.compile(r"\bremote\b", re.I)
_TAG = re.compile(r"<[^>]+>")
_API = "https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true"


class AshbyScraper(Scraper):
    source = "ashby"

    def __init__(self, orgs: list[str] | None = None):
        self.orgs = orgs if orgs is not None else settings.ashby_orgs_list()

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        for org in self.orgs:
            try:
                resp = httpx.get(
                    _API.format(org=org),
                    headers={"User-Agent": "JobHunterAI/0.1"},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                log.warning("ashby_fetch_failed", org=org, error=str(exc))
                continue
            for j in data.get("jobs", []):
                loc = j.get("location", "") or ""
                desc = j.get("descriptionPlain") or _TAG.sub("", j.get("descriptionHtml", ""))
                remote = bool(j.get("isRemote")) or bool(_REMOTE.search(f"{loc} {desc[:400]}"))
                jobs.append(
                    RawJob(
                        source=self.source,
                        external_id=str(j.get("id")),
                        title=j.get("title", ""),
                        company=org,
                        location=loc,
                        remote=remote,
                        description=desc[:6000],
                        apply_url=j.get("jobUrl", "") or j.get("applyUrl", ""),
                        raw={"org": org, "ashby_id": j.get("id")},
                    )
                )
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
        log.info("ashby_fetched", count=len(jobs), orgs=len(self.orgs))
        return jobs
