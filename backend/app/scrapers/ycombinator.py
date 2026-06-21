"""Y Combinator jobs connector via the public HN Algolia API (hiring posts).

Pulls roles from the latest 'Ask HN: Who is hiring?' thread. This is a public,
documented API. For the full YC 'Work at a Startup' board you must use their
authenticated product — left as an extension point.
"""

from __future__ import annotations

import re

import httpx

from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.yc")
_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
_ITEM = "https://hn.algolia.com/api/v1/items/{id}"
_REMOTE = re.compile(r"\bremote\b", re.I)


class YCombinatorScraper(Scraper):
    source = "ycombinator"

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        try:
            story = httpx.get(
                _SEARCH,
                params={"query": "Ask HN: Who is hiring?", "tags": "story", "hitsPerPage": 1},
                timeout=30,
            ).json()
            hits = story.get("hits", [])
            if not hits:
                return []
            thread_id = hits[0]["objectID"]
            data = httpx.get(_ITEM.format(id=thread_id), timeout=30).json()
        except Exception as exc:  # noqa: BLE001
            log.warning("yc_fetch_failed", error=str(exc))
            return []

        jobs: list[RawJob] = []
        for child in data.get("children", []):
            text = (child.get("text") or "").replace("<p>", "\n").strip()
            if not text:
                continue
            first_line = re.sub(r"<[^>]+>", "", text.splitlines()[0])[:200]
            company = first_line.split("|")[0].strip()[:120] or "YC startup"
            jobs.append(
                RawJob(
                    source=self.source,
                    external_id=str(child.get("id")),
                    title=first_line,
                    company=company,
                    location="Remote" if _REMOTE.search(text) else "",
                    remote=bool(_REMOTE.search(text)),
                    description=re.sub(r"<[^>]+>", "", text)[:4000],
                    apply_url=f"https://news.ycombinator.com/item?id={child.get('id')}",
                )
            )
            if len(jobs) >= limit:
                break
        log.info("yc_fetched", count=len(jobs))
        return jobs
