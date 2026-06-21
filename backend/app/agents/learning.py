"""Agent 9 — Learning. Analyze outcomes, recommend improvements, tune thresholds.

Simple reinforcement loop: resume variants accrue sends/responses/interviews; the agent
computes per-variant effectiveness and recommends the best performer + keyword/outreach
tweaks. Recommendations are persisted as a Setting and surfaced in the dashboard.
"""

from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.db.models import Application, ApplicationStatus, Resume, Setting


class LearningAgent(BaseAgent):
    name = "learning"

    def variant_performance(self, user_id: str) -> dict:
        rows = self.db.query(Resume).filter(Resume.user_id == user_id).all()
        agg: dict[str, dict] = {}
        for r in rows:
            b = agg.setdefault(r.variant, {"sends": 0, "responses": 0, "interviews": 0})
            b["sends"] += r.sends
            b["responses"] += r.responses
            b["interviews"] += r.interviews
        for v, b in agg.items():
            b["response_rate"] = round(b["responses"] / b["sends"] * 100, 1) if b["sends"] else 0.0
            b["interview_rate"] = round(b["interviews"] / b["sends"] * 100, 1) if b["sends"] else 0.0
        return agg

    def run(self, user_id: str) -> dict:
        perf = self.variant_performance(user_id)
        best = max(perf, key=lambda v: perf[v]["interview_rate"], default="A") if perf else "A"

        apps = self.db.query(Application).filter(Application.user_id == user_id).all()
        applied = [a for a in apps if a.status != ApplicationStatus.pending]
        rejected = sum(1 for a in apps if a.status == ApplicationStatus.rejected)
        positive = sum(
            1 for a in apps if a.status in (ApplicationStatus.interview, ApplicationStatus.offer)
        )

        recs: list[str] = []
        if applied and positive / max(len(applied), 1) < 0.1:
            recs.append("Low interview rate — raise MATCH_THRESHOLD to target stronger-fit roles.")
        if rejected > positive * 3 and rejected > 5:
            recs.append("High rejection ratio — refine resume keywords toward required skills.")
        recs.append(f"Best-performing resume variant: {best}. Prefer it for new applications.")

        result = {
            "best_variant": best,
            "variant_performance": perf,
            "recommendations": recs,
        }
        self._save(user_id, result)
        self.audit("learning_run", best_variant=best)
        self.log.info("learning_done", best_variant=best)
        return result

    def _save(self, user_id: str, result: dict) -> None:
        setting = (
            self.db.query(Setting)
            .filter(Setting.user_id == user_id, Setting.key == "learning_recommendations")
            .one_or_none()
        )
        if not setting:
            setting = Setting(user_id=user_id, key="learning_recommendations")
            self.db.add(setting)
        setting.value = json.dumps(result)
        self.db.commit()
