"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth / users ----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    is_admin: bool = False


class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    automation_paused: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---- profile ----
class ProfileIn(BaseModel):
    master_resume: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    min_salary: int = 0
    remote_only: bool = False
    years_experience: float = 0.0


class ProfileOut(ProfileIn, ORMModel):
    id: str
    user_id: str


# ---- jobs ----
class JobOut(ORMModel):
    id: str
    source: str
    title: str
    company: str
    location: str
    remote: bool
    salary_min: int
    salary_max: int
    experience_years: float
    description: str
    apply_url: str
    analyzed: bool
    match_score: float
    score_breakdown: dict
    required_skills: list
    preferred_skills: list
    created_at: datetime


class JobFilter(BaseModel):
    min_score: float | None = None
    company: str | None = None
    remote: bool | None = None
    source: str | None = None
    limit: int = 50
    offset: int = 0


# ---- applications ----
class ApplicationOut(ORMModel):
    id: str
    job_id: str
    status: str
    submitted_at: datetime | None
    answers: dict
    screenshots: list
    confirmation: str
    error: str
    needs_review_reason: str
    created_at: datetime


class ApplicationCreate(BaseModel):
    job_id: str
    auto_submit: bool = True


# ---- resumes / cover letters ----
class ResumeOut(ORMModel):
    id: str
    job_id: str | None
    variant: str
    version: int
    content: str
    keywords: list
    pdf_path: str
    docx_path: str
    sends: int
    responses: int
    interviews: int
    created_at: datetime


class CoverLetterOut(ORMModel):
    id: str
    job_id: str | None
    content: str
    pdf_path: str
    docx_path: str
    created_at: datetime


# ---- recruiters / messages ----
class RecruiterOut(ORMModel):
    id: str
    name: str
    title: str
    company: str
    email: str
    linkedin_url: str
    source: str


class MessageOut(ORMModel):
    id: str
    recruiter_id: str
    channel: str
    sequence_step: int
    subject: str
    body: str
    status: str
    sent_at: datetime | None
    created_at: datetime


# ---- analytics ----
class Analytics(BaseModel):
    applications_today: int
    applications_week: int
    total_applications: int
    interview_rate: float
    response_rate: float
    offer_rate: float
    by_status: dict[str, int]
    by_source: dict[str, int]


# ---- settings / admin ----
class SettingIn(BaseModel):
    key: str
    value: str
    encrypted: bool = False


class CompanyRuleIn(BaseModel):
    company: str
    kind: str = "blacklist"  # blacklist | whitelist


class AdminConfig(BaseModel):
    automation_paused: bool | None = None
    match_threshold: int | None = None
    max_applications_per_day: int | None = None
