"""Y Combinator-adjacent jobs via the public HN Algolia API.

Pulls roles from the latest official monthly *"Ask HN: Who is hiring?"* thread, which is
always posted by the `whoishiring` account. We resolve that exact thread (not any random
story that merely contains those words) and treat each TOP-LEVEL comment as one job post.

This is a public, documented API. For the full YC 'Work at a Startup' board you must use
their authenticated product — left as an extension point.
"""

from __future__ import annotations

import re

import httpx

from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.yc")
# search_by_date => newest first, so we always resolve the *current* month's thread.
_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
_ITEM = "https://hn.algolia.com/api/v1/items/{id}"
_REMOTE = re.compile(r"\bremote\b", re.I)
_TAG = re.compile(r"<[^>]+>")
_TITLE_OK = re.compile(r"^ask hn:\s*who is hiring", re.I)


def _clean(html: str) -> str:
    text = (html or "").replace("<p>", "\n").replace("</p>", "")
    text = text.replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&")
    text = text.replace("&#x2F;", "/").replace("&gt;", ">").replace("&lt;", "<")
    return _TAG.sub("", text).strip()


class YCombinatorScraper(Scraper):
    source = "ycombinator"

    def _latest_thread_id(self) -> str | None:
        """Find the most recent official 'Who is hiring?' thread by the whoishiring user."""
        try:
            resp = httpx.get(
                _SEARCH,
                params={
                    "tags": "story,author_whoishiring",
                    "query": "who is hiring",
                    "hitsPerPage": 20,
                },
                timeout=30,
            ).json()
        except Exception as exc:  # noqa: BLE001
            log.warning("yc_search_failed", error=str(exc))
            return None
        candidates = [
            h for h in resp.get("hits", []) if _TITLE_OK.match((h.get("title") or "").strip())
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda h: h.get("created_at_i", 0), reverse=True)
        return candidates[0]["objectID"]

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        thread_id = self._latest_thread_id()
        if not thread_id:
            log.warning("yc_no_thread")
            return []
        try:
            data = httpx.get(_ITEM.format(id=thread_id), timeout=30).json()
        except Exception as exc:  # noqa: BLE001
            log.warning("yc_item_failed", error=str(exc))
            return []

        jobs: list[RawJob] = []
        for child in data.get("children", []):
            if child.get("author") == "whoishiring":
                continue  # skip the poster's own sub-threads
            text = _clean(child.get("text") or "")
            if not text or len(text) < 30:
                continue
            first_line = text.splitlines()[0][:200]
            # Typical format: "Company | Role | Location | Remote | ..."
            parts = [p.strip() for p in first_line.split("|")]
            company = parts[0][:120] or "YC startup"
            title = (parts[1] if len(parts) > 1 else first_line)[:200]
            remote = bool(_REMOTE.search(text))
            jobs.append(
                RawJob(
                    source=self.source,
                    external_id=str(child.get("id")),
                    title=title,
                    company=company,
                    location="Remote" if remote else (parts[2] if len(parts) > 2 else ""),
                    remote=remote,
                    description=text[:4000],
                    apply_url=f"https://news.ycombinator.com/item?id={child.get('id')}",
                )
            )
            if len(jobs) >= limit:
                break
        log.info("yc_fetched", count=len(jobs), thread=thread_id)
        return jobs
