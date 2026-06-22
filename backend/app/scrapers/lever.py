"""Lever job-board connector — public JSON API.

    https://api.lever.co/v0/postings/{company}?mode=json

`company` is the slug in jobs.lever.co/<company>. Configure via LEVER_COMPANIES
(comma-separated). No auth needed to read postings.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.lever")
_REMOTE = re.compile(r"\bremote\b", re.I)
_API = "https://api.lever.co/v0/postings/{company}?mode=json"


class LeverScraper(Scraper):
    source = "lever"

    def __init__(self, companies: list[str] | None = None):
        self.companies = companies if companies is not None else settings.lever_companies_list()

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        for company in self.companies:
            try:
                resp = httpx.get(
                    _API.format(company=company),
                    headers={"User-Agent": "JobHunterAI/0.1"},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                log.warning("lever_fetch_failed", company=company, error=str(exc))
                continue
            for p in data:
                cats = p.get("categories") or {}
                loc = cats.get("location", "")
                desc = p.get("descriptionPlain") or p.get("description", "")
                remote = bool(_REMOTE.search(f"{loc} {cats.get('commitment','')} {desc[:400]}"))
                jobs.append(
                    RawJob(
                        source=self.source,
                        external_id=str(p.get("id")),
                        title=p.get("text", ""),
                        company=company,
                        location=loc,
                        remote=remote,
                        description=desc[:6000],
                        apply_url=p.get("hostedUrl", "") or p.get("applyUrl", ""),
                        raw={"company": company, "lever_id": p.get("id")},
                    )
                )
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
        log.info("lever_fetched", count=len(jobs), companies=len(self.companies))
        return jobs
