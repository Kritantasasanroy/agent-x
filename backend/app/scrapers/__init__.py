"""Job source connectors. Enable only sources you are permitted to use."""

from __future__ import annotations

from app.core.config import settings
from app.scrapers.ashby import AshbyScraper
from app.scrapers.base import RawJob, Scraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.restricted import (
    FounditScraper,
    GlassdoorScraper,
    IndeedScraper,
    LinkedInScraper,
    NaukriScraper,
    WellfoundScraper,
)
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.scrapers.ycombinator import YCombinatorScraper

_REGISTRY: dict[str, type[Scraper]] = {
    "remoteok": RemoteOKScraper,
    "weworkremotely": WeWorkRemotelyScraper,
    "ycombinator": YCombinatorScraper,
    "greenhouse": GreenhouseScraper,
    "lever": LeverScraper,
    "ashby": AshbyScraper,
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "naukri": NaukriScraper,
    "glassdoor": GlassdoorScraper,
    "wellfound": WellfoundScraper,
    "foundit": FounditScraper,
}


def active_scrapers() -> list[Scraper]:
    return [_REGISTRY[name]() for name in settings.enabled_scrapers() if name in _REGISTRY]


__all__ = ["RawJob", "Scraper", "active_scrapers"]
