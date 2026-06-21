"""Agent 2 — Job Analysis. Extract requirements + compute a 0–100 match score.

Scoring is deterministic (works offline). Weighted blend of:
  skills (40) · experience (20) · location (15) · salary (15) · remote (10)
"""

from __future__ import annotations

import re

from app.agents.base import BaseAgent
from app.db.models import Job, Profile

_SKILL_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,29}")
# A compact, extendable tech lexicon used to pull skills out of free text.
_LEXICON = {
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++", "c#",
    "react", "next.js", "nextjs", "node", "node.js", "vue", "angular", "django", "fastapi",
    "flask", "spring", "express", "postgres", "postgresql", "mysql", "mongodb", "redis",
    "kafka", "rabbitmq", "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform",
    "ansible", "ci/cd", "graphql", "rest", "grpc", "tensorflow", "pytorch", "pandas",
    "numpy", "sql", "nosql", "celery", "playwright", "selenium", "html", "css", "tailwind",
    "git", "linux", "bash", "spark", "airflow", "snowflake", "llm", "nlp", "ml",
}


class AnalysisAgent(BaseAgent):
    name = "analysis"

    def extract_skills(self, text: str) -> list[str]:
        found = set()
        low = text.lower()
        for token in _SKILL_RE.findall(low):
            if token in _LEXICON:
                found.add(token)
        # multi-word terms
        for term in ("ci/cd", "node.js", "next.js"):
            if term in low:
                found.add(term)
        return sorted(found)

    def _experience_years(self, text: str) -> float:
        m = re.search(r"(\d{1,2})\s*\+?\s*(?:years|yrs)", text.lower())
        return float(m.group(1)) if m else 0.0

    def score(self, job: Job, profile: Profile) -> tuple[float, dict]:
        req = self.extract_skills(f"{job.title} {job.description}")
        prof_skills = {s.lower() for s in (profile.skills or [])}

        # skills (40)
        overlap = len([s for s in req if s in prof_skills])
        skills_score = (overlap / len(req)) * 40 if req else 24.0

        # experience (20)
        need = job.experience_years or self._experience_years(job.description)
        have = profile.years_experience or 0
        if need <= 0:
            exp_score = 16.0
        elif have >= need:
            exp_score = 20.0
        else:
            exp_score = max(0.0, 20.0 * (have / need))

        # location (15)
        prefs = [p.lower() for p in (profile.preferred_locations or [])]
        loc = (job.location or "").lower()
        if job.remote or not prefs:
            loc_score = 15.0
        elif any(p in loc or loc in p for p in prefs):
            loc_score = 15.0
        else:
            loc_score = 5.0

        # salary (15)
        want = profile.min_salary or 0
        offer = job.salary_max or job.salary_min or 0
        if want <= 0 or offer <= 0:
            sal_score = 11.0
        elif offer >= want:
            sal_score = 15.0
        else:
            sal_score = max(0.0, 15.0 * (offer / want))

        # remote (10)
        remote_score = 10.0 if (job.remote or not profile.remote_only) else 0.0

        total = round(skills_score + exp_score + loc_score + sal_score + remote_score, 1)
        breakdown = {
            "skills": round(skills_score, 1),
            "experience": round(exp_score, 1),
            "location": round(loc_score, 1),
            "salary": round(sal_score, 1),
            "remote": round(remote_score, 1),
            "matched_skills": [s for s in req if s in prof_skills],
        }
        return min(total, 100.0), breakdown

    def run(self, job: Job, profile: Profile) -> dict:
        req = self.extract_skills(f"{job.title} {job.description}")
        total, breakdown = self.score(job, profile)
        job.required_skills = req
        job.preferred_skills = [s for s in req if s not in {x.lower() for x in (profile.skills or [])}]
        job.match_score = total
        job.score_breakdown = breakdown
        job.analyzed = True
        self.db.commit()
        self.log.info("job_analyzed", job_id=job.id, score=total)
        return {"score": total, "breakdown": breakdown}
