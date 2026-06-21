"""ToS-restricted source connectors.

These platforms (LinkedIn, Indeed, Naukri, Glassdoor, Wellfound, Foundit) prohibit
automated scraping in their Terms of Service. They ship as **disabled stubs**. To use a
site, obtain proper access (official API / partner program / your own permitted account)
and implement `fetch()` accordingly. The framework will not scrape them for you.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.scrapers.base import RawJob, Scraper

log = get_logger("scraper.restricted")


class _RestrictedStub(Scraper):
    source = "restricted"

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        log.warning(
            "restricted_source_disabled",
            source=self.source,
            note="Implement with an authorized/official API before enabling.",
        )
        return []


class LinkedInScraper(_RestrictedStub):
    source = "linkedin"
    # TODO(stub): integrate LinkedIn's official Talent / Jobs API with proper auth.


class IndeedScraper(_RestrictedStub):
    source = "indeed"
    # TODO(stub): use Indeed Publisher/Employer API where permitted.


class NaukriScraper(_RestrictedStub):
    source = "naukri"


class GlassdoorScraper(_RestrictedStub):
    source = "glassdoor"


class WellfoundScraper(_RestrictedStub):
    source = "wellfound"


class FounditScraper(_RestrictedStub):
    source = "foundit"
