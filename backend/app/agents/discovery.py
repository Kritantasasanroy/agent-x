"""Agent 1 — Job Discovery. Search sources, dedupe, persist."""

from __future__ import annotations

from sqlalchemy import select

from app.agents.base import BaseAgent
from app.db.models import Job
from app.scrapers import active_scrapers
from app.services.vector_store import get_vector_store


class DiscoveryAgent(BaseAgent):
    name = "discovery"

    def run(self, queries: list[str] | None = None, limit_per_source: int = 50) -> dict:
        store = get_vector_store()
        seen_fp = {fp for (fp,) in self.db.execute(select(Job.fingerprint)).all() if fp}
        added = 0
        skipped = 0

        for scraper in active_scrapers():
            for raw in scraper.fetch(queries=queries, limit=limit_per_source):
                fp = raw.fingerprint()
                exists = self.db.execute(
                    select(Job).where(Job.source == raw.source, Job.external_id == raw.external_id)
                ).scalar_one_or_none()
                if exists or fp in seen_fp:
                    skipped += 1
                    continue
                job = Job(
                    source=raw.source,
                    external_id=raw.external_id,
                    fingerprint=fp,
                    title=raw.title,
                    company=raw.company,
                    location=raw.location,
                    remote=raw.remote,
                    salary_min=raw.salary_min,
                    salary_max=raw.salary_max,
                    experience_years=raw.experience_years,
                    description=raw.description,
                    apply_url=raw.apply_url,
                    raw=raw.raw,
                )
                self.db.add(job)
                self.db.flush()
                seen_fp.add(fp)
                added += 1
                try:
                    store.upsert(
                        job.id,
                        f"{job.title}\n{job.company}\n{job.description}",
                        {"company": job.company, "source": job.source},
                    )
                except Exception as exc:  # noqa: BLE001
                    self.log.warning("vector_upsert_failed", error=str(exc))

        self.db.commit()
        self.audit("discovery_run", added=added, skipped=skipped)
        self.log.info("discovery_done", added=added, skipped=skipped)
        return {"added": added, "skipped": skipped}
