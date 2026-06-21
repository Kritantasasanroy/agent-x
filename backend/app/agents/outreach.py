"""Agent 6 — Recruiter Outreach. Personalized cold messages + follow-up sequence.

Sequence: step 0 = initial, step 1 = +7 days, step 2 = +14 days. Stops on reply.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent
from app.db.models import Job, Message, MessageStatus, Profile, Recruiter, Response
from app.services.email import send_email

SYSTEM = """Write a short, personalized cold outreach email to a recruiter / founder.
Reference the company, the role, and one genuine, specific reason the candidate fits.
No spammy phrasing, no exaggeration. 90-150 words. Output JSON:
{"subject": "...", "body": "..."}"""

FOLLOWUP_DAYS = {0: 0, 1: 7, 2: 14}


class OutreachAgent(BaseAgent):
    name = "outreach"

    def compose(self, recruiter: Recruiter, profile: Profile, job: Job | None, step: int) -> dict:
        ctx = (
            f"RECRUITER: {recruiter.name} ({recruiter.title}) at {recruiter.company}\n"
            f"CANDIDATE: {profile.user.full_name if profile.user else ''} — "
            f"skills {', '.join((profile.skills or [])[:8])}\n"
            f"ROLE: {job.title if job else 'open roles'}\n"
            f"PORTFOLIO: {profile.portfolio_url} GitHub: {profile.github_url}\n"
            f"SEQUENCE STEP: {step} (0=initial,1=first follow-up,2=second follow-up)"
        )
        data = self.llm.json(SYSTEM, ctx, max_tokens=400)
        if not data.get("body"):
            role = job.title if job else "opportunities"
            data = {
                "subject": f"{profile.user.full_name if profile.user else 'Candidate'} — {role} at {recruiter.company}",
                "body": (
                    f"Hi {recruiter.name or 'there'},\n\n"
                    f"I'm reaching out about {role} at {recruiter.company}. My background in "
                    f"{', '.join((profile.skills or [])[:4])} maps closely to what you're building. "
                    f"Portfolio: {profile.portfolio_url}. Open to a quick chat?\n\n"
                    f"Best,\n{profile.user.full_name if profile.user else ''}"
                ),
            }
        return data

    def queue_initial(self, recruiter: Recruiter, profile: Profile, job: Job | None) -> Message:
        return self._create_step(recruiter, profile, job, step=0, send_now=True)

    def _create_step(self, recruiter, profile, job, step, send_now) -> Message:
        data = self.compose(recruiter, profile, job, step)
        scheduled = datetime.now(timezone.utc) + timedelta(days=FOLLOWUP_DAYS[step])
        msg = Message(
            user_id=profile.user_id,
            recruiter_id=recruiter.id,
            job_id=job.id if job else None,
            sequence_step=step,
            subject=data["subject"],
            body=data["body"],
            scheduled_for=scheduled,
        )
        self.db.add(msg)
        self.db.commit()
        if send_now:
            self.send(msg, recruiter)
        return msg

    def send(self, msg: Message, recruiter: Recruiter) -> None:
        ok = send_email(recruiter.email, msg.subject, msg.body) if recruiter.email else False
        msg.status = MessageStatus.sent if ok else MessageStatus.queued
        msg.sent_at = datetime.now(timezone.utc) if ok else None
        self.db.commit()
        self.audit("outreach_sent" if ok else "outreach_queued", target=recruiter.id, step=msg.sequence_step)

    def process_followups(self) -> int:
        """Send due follow-ups for sequences with no reply yet."""
        now = datetime.now(timezone.utc)
        due = (
            self.db.query(Message)
            .filter(Message.status == MessageStatus.queued, Message.scheduled_for <= now)
            .all()
        )
        sent = 0
        for msg in due:
            replied = (
                self.db.query(Response).join(Message).filter(Message.recruiter_id == msg.recruiter_id).count()
            )
            if replied:
                continue
            recruiter = self.db.get(Recruiter, msg.recruiter_id)
            if recruiter:
                self.send(msg, recruiter)
                sent += 1
        return sent
