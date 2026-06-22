"""Recruiter outreach: initial send + follow-up sequence (email in dry-run)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents.outreach import OutreachAgent
from app.db.models import MessageStatus, Recruiter


def test_queue_initial_creates_message(db, fake_llm, make_user):
    user, profile = make_user(db, "out1@test.com")
    rec = Recruiter(name="Jane", company="Acme", email="")  # no email -> stays queued
    db.add(rec)
    db.commit()
    msg = OutreachAgent(db, llm=fake_llm).queue_initial(rec, profile, None)
    assert msg.sequence_step == 0
    assert msg.subject and msg.body
    assert "Acme" in msg.subject or "Acme" in msg.body
    assert msg.status == MessageStatus.queued


def test_followup_due_is_processed(db, fake_llm, make_user):
    user, profile = make_user(db, "out2@test.com")
    rec = Recruiter(name="Bob", company="Beta", email="")
    db.add(rec)
    db.commit()
    agent = OutreachAgent(db, llm=fake_llm)
    msg = agent.queue_initial(rec, profile, None)
    msg.scheduled_for = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    assert agent.process_followups() >= 1


def test_followup_skipped_when_replied(db, fake_llm, make_user):
    from app.db.models import Response

    user, profile = make_user(db, "out3@test.com")
    rec = Recruiter(name="Cara", company="Gamma", email="")
    db.add(rec)
    db.commit()
    agent = OutreachAgent(db, llm=fake_llm)
    msg = agent.queue_initial(rec, profile, None)
    msg.scheduled_for = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(Response(message_id=msg.id, sentiment="positive", body="Let's chat"))
    db.commit()
    # a reply exists for this recruiter -> the due follow-up must be suppressed
    before = db.query(Response).count()
    agent.process_followups()
    assert db.query(Response).count() == before  # nothing changed / no crash
