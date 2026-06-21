"""initial schema

Creates all tables from the SQLAlchemy metadata. For fine-grained migrations going
forward use `alembic revision --autogenerate -m "..."`.

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""
from __future__ import annotations

from alembic import op  # noqa: F401

from app.db.base import Base
from app.db import models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
