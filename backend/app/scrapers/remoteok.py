"""RemoteOK connector — uses their public JSON feed (https://remoteok.com/api)."""

from __future__ import annotations

import re

import httpx

from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.remoteok")
_TAG = re.compile(r"<[^>]+>")


class RemoteOKScraper(Scraper):
    source = "remoteok"
    URL = "https://remoteok.com/api"

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        try:
            resp = httpx.get(self.URL, headers={"User-Agent": "JobHunterAI/0.1"}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            log.warning("remoteok_fetch_failed", error=str(exc))
            return []

        jobs: list[RawJob] = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue  # first element is legal notice
            desc = _TAG.sub("", item.get("description", "")).strip()
            jobs.append(
                RawJob(
                    source=self.source,
                    external_id=str(item.get("id")),
                    title=item.get("position", ""),
                    company=item.get("company", ""),
                    location=item.get("location", "Remote") or "Remote",
                    remote=True,
                    salary_min=int(item.get("salary_min") or 0),
                    salary_max=int(item.get("salary_max") or 0),
                    description=desc,
                    apply_url=item.get("url", ""),
                    raw={"tags": item.get("tags", [])},
                )
            )
            if len(jobs) >= limit:
                break
        log.info("remoteok_fetched", count=len(jobs))
        return jobs
