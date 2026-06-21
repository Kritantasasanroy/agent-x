"""Base agent: shared db session, llm, logging, and audit helper."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db import session as db_session
from app.db.models import AuditLog
from app.services.llm import LLMClient, get_llm


class BaseAgent:
    name: str = "agent"

    def __init__(self, db: Session | None = None, llm: LLMClient | None = None) -> None:
        self._own_db = db is None
        self.db: Session = db or db_session.session()
        self.llm = llm or get_llm()
        self.log = get_logger(self.name)

    def audit(self, action: str, target: str = "", **meta) -> None:
        self.db.add(AuditLog(actor=self.name, action=action, target=target, meta=meta))
        self.db.commit()

    def close(self) -> None:
        if self._own_db:
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()
