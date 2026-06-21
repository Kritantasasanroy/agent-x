"""All ORM models — the tracking schema for JobHunter AI."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Role(str, enum.Enum):
    admin = "admin"
    user = "user"


class ApplicationStatus(str, enum.Enum):
    pending = "pending"          # queued, not yet submitted
    needs_review = "needs_review"  # human action required (e.g. CAPTCHA)
    applied = "applied"
    interview = "interview"
    rejected = "rejected"
    offer = "offer"
    withdrawn = "withdrawn"
    failed = "failed"


class MessageChannel(str, enum.Enum):
    email = "email"
    linkedin = "linkedin"
    form = "form"


class MessageStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    replied = "replied"
    bounced = "bounced"
    failed = "failed"


# --------------------------------------------------------------------------- #
# Users + profile
# --------------------------------------------------------------------------- #
class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[Role] = mapped_column(String(20), default=Role.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # automation switch — admin can pause everything
    automation_paused: Mapped[bool] = mapped_column(Boolean, default=False)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
    applications: Mapped[list["Application"]] = relationship(back_populates="user")


class Profile(UUIDMixin, TimestampMixin, Base):
    """The user-supplied master profile that drives everything."""

    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    master_resume: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    linkedin_url: Mapped[str] = mapped_column(String(255), default="")
    github_url: Mapped[str] = mapped_column(String(255), default="")
    portfolio_url: Mapped[str] = mapped_column(String(255), default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    experience: Mapped[list] = mapped_column(JSON, default=list)
    education: Mapped[list] = mapped_column(JSON, default=list)
    preferred_roles: Mapped[list] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list)
    min_salary: Mapped[int] = mapped_column(Integer, default=0)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False)
    years_experience: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped[User] = relationship(back_populates="profile")


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
class Job(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_job_source_extid"),)

    source: Mapped[str] = mapped_column(String(50), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, default="")  # dedupe hash
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), default="")
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    salary_max: Mapped[int] = mapped_column(Integer, default=0)
    experience_years: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text, default="")
    apply_url: Mapped[str] = mapped_column(String(1024), default="")
    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    # analysis output
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSON, default=list)

    applications: Mapped[list["Application"]] = relationship(back_populates="job")


# --------------------------------------------------------------------------- #
# Resumes + Cover letters
# --------------------------------------------------------------------------- #
class Resume(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    variant: Mapped[str] = mapped_column(String(10), default="A")  # A/B/C test bucket
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    pdf_path: Mapped[str] = mapped_column(String(1024), default="")
    docx_path: Mapped[str] = mapped_column(String(1024), default="")
    # learning signals
    sends: Mapped[int] = mapped_column(Integer, default=0)
    responses: Mapped[int] = mapped_column(Integer, default=0)
    interviews: Mapped[int] = mapped_column(Integer, default=0)


class CoverLetter(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cover_letters"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str] = mapped_column(String(1024), default="")
    docx_path: Mapped[str] = mapped_column(String(1024), default="")


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    cover_letter_id: Mapped[str | None] = mapped_column(ForeignKey("cover_letters.id"), nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(String(20), default=ApplicationStatus.pending)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)        # open-ended Q&A
    screenshots: Mapped[list] = mapped_column(JSON, default=list)    # file paths
    confirmation: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    needs_review_reason: Mapped[str] = mapped_column(String(255), default="")

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="application")


# --------------------------------------------------------------------------- #
# Outreach
# --------------------------------------------------------------------------- #
class Recruiter(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recruiters"

    name: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    company: Mapped[str] = mapped_column(String(255), index=True, default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    linkedin_url: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(100), default="")

    messages: Mapped[list["Message"]] = relationship(back_populates="recruiter")


class Message(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    recruiter_id: Mapped[str] = mapped_column(ForeignKey("recruiters.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    channel: Mapped[MessageChannel] = mapped_column(String(20), default=MessageChannel.email)
    sequence_step: Mapped[int] = mapped_column(Integer, default=0)  # 0=initial,1=+7d,2=+14d
    subject: Mapped[str] = mapped_column(String(512), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[MessageStatus] = mapped_column(String(20), default=MessageStatus.queued)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recruiter: Mapped[Recruiter] = relationship(back_populates="messages")
    responses: Mapped[list["Response"]] = relationship(back_populates="message")


class Response(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "responses"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), index=True)
    sentiment: Mapped[str] = mapped_column(String(20), default="neutral")  # positive/neutral/negative
    body: Mapped[str] = mapped_column(Text, default="")

    message: Mapped[Message] = relationship(back_populates="responses")


class Interview(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    round_name: Mapped[str] = mapped_column(String(100), default="")
    prep_packet: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")

    application: Mapped[Application] = relationship(back_populates="interviews")


# --------------------------------------------------------------------------- #
# Admin / ops
# --------------------------------------------------------------------------- #
class CompanyRule(UUIDMixin, TimestampMixin, Base):
    """Whitelist / blacklist of companies."""

    __tablename__ = "company_rules"
    __table_args__ = (UniqueConstraint("company", name="uq_company_rule"),)

    company: Mapped[str] = mapped_column(String(255), index=True)
    kind: Mapped[str] = mapped_column(String(20), default="blacklist")  # blacklist|whitelist


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor: Mapped[str] = mapped_column(String(255), default="system")
    action: Mapped[str] = mapped_column(String(255))
    target: Mapped[str] = mapped_column(String(255), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class Setting(UUIDMixin, TimestampMixin, Base):
    """Encrypted-value key/value store (per user or global)."""

    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_setting_user_key"),)

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
