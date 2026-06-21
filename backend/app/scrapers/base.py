"""Scraper interface + the normalized RawJob record."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    company: str
    location: str = ""
    remote: bool = False
    salary_min: int = 0
    salary_max: int = 0
    experience_years: float = 0.0
    description: str = ""
    apply_url: str = ""
    raw: dict = field(default_factory=dict)

    def fingerprint(self) -> str:
        """Stable hash for cross-source dedupe (company + title + location)."""
        key = re.sub(r"\s+", " ", f"{self.company}|{self.title}|{self.location}".lower()).strip()
        return hashlib.sha256(key.encode()).hexdigest()


class Scraper:
    source: str = "base"
    enabled_by_default: bool = True

    def fetch(self, queries: list[str] | None = None, limit: int = 50) -> list[RawJob]:
        """Return normalized jobs. Implementations must be polite (rate-limited)."""
        raise NotImplementedError
