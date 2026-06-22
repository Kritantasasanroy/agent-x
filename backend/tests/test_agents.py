"""Resume, cover letter, interview, tracking, and learning agents."""

from __future__ import annotations

import os

from app.agents.cover_letter import CoverLetterAgent
from app.agents.interview import InterviewAgent
from app.agents.learning import LearningAgent
from app.agents.resume import ResumeAgent
from app.agents.tracking import TrackingAgent
from app.db.models import Application, ApplicationStatus, Resume


def test_resume_generation_writes_files(db, fake_llm, make_user, make_job):
    user, profile = make_user(db, "resume@test.com")
    job = make_job(db, ext="r1")
    resume = ResumeAgent(db, llm=fake_llm).run(job, profile, variant="A")
    assert resume.content
    assert resume.variant == "A"
    assert os.path.exists(resume.pdf_path)
    assert os.path.exists(resume.docx_path)


def test_resume_never_blank_on_offline_fallback(db, make_user, make_job):
    """With the real (offline) LLM the resume must still be produced from profile facts."""
    user, profile = make_user(db, "resume2@test.com")
    job = make_job(db, ext="r2")
    resume = ResumeAgent(db).run(job, profile, variant="B")  # real llm -> offline fallback
    assert profile.master_resume[:10] in resume.content or "SKILLS" in resume.content


def test_cover_letter_generation(db, fake_llm, make_user, make_job):
    user, profile = make_user(db, "cover@test.com")
    job = make_job(db, ext="c1")
    cover = CoverLetterAgent(db, llm=fake_llm).run(job, profile)
    assert cover.content
    assert os.path.exists(cover.pdf_path)


def test_interview_prep_fallback(db, make_user, make_job):
    user, profile = make_user(db, "interview@test.com")
    job = make_job(db, ext="i1")
    application = Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.interview)
    db.add(application)
    db.commit()
    interview = InterviewAgent(db).run(application)  # offline -> deterministic packet
    assert interview.prep_packet
    assert "technical_questions" in interview.prep_packet


def test_tracking_analytics_counts(db, make_user, make_job):
    user, _ = make_user(db, "track@test.com")
    job = make_job(db, ext="t1")
    db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.applied))
    db.add(Application(user_id=user.id, job_id=job.id, status=ApplicationStatus.interview))
    db.commit()
    metrics = TrackingAgent(db).analytics(user_id=user.id)
    assert metrics["total_applications"] >= 2
    assert metrics["interview_rate"] > 0  # 1 interview / 2 applied-or-better


def test_learning_recommends_best_variant(db, make_user):
    user, _ = make_user(db, "learn@test.com")
    # variant B clearly outperforms A
    db.add(Resume(user_id=user.id, variant="A", sends=10, responses=1, interviews=0))
    db.add(Resume(user_id=user.id, variant="B", sends=10, responses=6, interviews=4))
    db.commit()
    result = LearningAgent(db).run(user.id)
    assert result["best_variant"] == "B"
    assert any("variant" in r.lower() for r in result["recommendations"])
