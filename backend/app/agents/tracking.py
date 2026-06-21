"""Agent 7 — Tracking. Pipeline status + dashboard metrics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.agents.base import BaseAgent
from app.db.models import Application, ApplicationStatus, Job, Message, MessageStatus, Response


class TrackingAgent(BaseAgent):
    name = "tracking"

    def analytics(self, user_id: str | None = None) -> dict:
        q = self.db.query(Application)
        if user_id:
            q = q.filter(Application.user_id == user_id)

        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week = today - timedelta(days=today.weekday())

        total = q.count()
        apps_today = q.filter(Application.created_at >= today).count()
        apps_week = q.filter(Application.created_at >= week).count()

        by_status: dict[str, int] = {}
        for status, count in (
            self.db.query(Application.status, func.count())
            .group_by(Application.status)
            .all()
        ):
            by_status[str(getattr(status, "value", status))] = count

        applied = sum(
            by_status.get(s, 0)
            for s in ("applied", "interview", "rejected", "offer")
        )
        interviews = by_status.get("interview", 0) + by_status.get("offer", 0)
        offers = by_status.get("offer", 0)

        # response rate from outreach
        sent = self.db.query(Message).filter(Message.status == MessageStatus.sent).count()
        replies = self.db.query(Response).count()

        by_source: dict[str, int] = {}
        for source, count in (
            self.db.query(Job.source, func.count())
            .join(Application, Application.job_id == Job.id)
            .group_by(Job.source)
            .all()
        ):
            by_source[source] = count

        return {
            "applications_today": apps_today,
            "applications_week": apps_week,
            "total_applications": total,
            "interview_rate": round(interviews / applied * 100, 1) if applied else 0.0,
            "response_rate": round(replies / sent * 100, 1) if sent else 0.0,
            "offer_rate": round(offers / applied * 100, 1) if applied else 0.0,
            "by_status": by_status,
            "by_source": by_source,
        }

    def set_status(self, application: Application, status: ApplicationStatus) -> None:
        application.status = status
        self.db.commit()
        self.audit("status_change", target=application.id, status=status)
