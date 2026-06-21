from types import SimpleNamespace

from app.agents.analysis import AnalysisAgent


def _agent():
    a = AnalysisAgent.__new__(AnalysisAgent)  # no DB needed for pure scoring
    return a


def test_extract_skills():
    skills = _agent().extract_skills("We need Python, FastAPI and Docker on AWS")
    assert "python" in skills and "fastapi" in skills and "docker" in skills and "aws" in skills


def test_score_strong_match_high():
    agent = _agent()
    job = SimpleNamespace(
        title="Senior Python Engineer",
        description="Python FastAPI Docker AWS, 3+ years",
        experience_years=3, remote=True, location="Remote",
        salary_min=100000, salary_max=140000,
    )
    profile = SimpleNamespace(
        skills=["Python", "FastAPI", "Docker", "AWS"], years_experience=5,
        preferred_locations=["Remote"], min_salary=90000, remote_only=False,
    )
    score, breakdown = agent.score(job, profile)
    assert score >= 75
    assert breakdown["skills"] > 0


def test_score_weak_match_low():
    agent = _agent()
    job = SimpleNamespace(
        title="Senior Rust Engineer",
        description="Rust systems programming, 8+ years",
        experience_years=8, remote=False, location="Berlin",
        salary_min=40000, salary_max=50000,
    )
    profile = SimpleNamespace(
        skills=["Python"], years_experience=1,
        preferred_locations=["New York"], min_salary=120000, remote_only=True,
    )
    score, _ = agent.score(job, profile)
    assert score < 75
