"""WeWorkRemotely connector — parses their public RSS feeds."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import httpx

from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.wwr")
_TAG = re.compile(r"<[^>]+>")
FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
]


class WeWorkRemotelyScraper(Scraper):
    source = "weworkremotely"

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        for feed in FEEDS:
            try:
                resp = httpx.get(feed, headers={"User-Agent": "JobHunterAI/0.1"}, timeout=30)
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
            except Exception as exc:  # noqa: BLE001
                log.warning("wwr_feed_failed", feed=feed, error=str(exc))
                continue
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                company, _, role = title.partition(":")
                link = (item.findtext("link") or "").strip()
                desc = _TAG.sub("", item.findtext("description") or "").strip()
                ext = link.rstrip("/").split("/")[-1] or link
                jobs.append(
                    RawJob(
                        source=self.source,
                        external_id=ext,
                        title=(role or title).strip(),
                        company=company.strip() or "Unknown",
                        location="Remote",
                        remote=True,
                        description=desc,
                        apply_url=link,
                    )
                )
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
        log.info("wwr_fetched", count=len(jobs))
        return jobs
