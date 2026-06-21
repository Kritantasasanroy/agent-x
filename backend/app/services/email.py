"""SMTP email sender for recruiter outreach. No-ops (logs) when SMTP unset."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("email")


def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_from:
        log.info("email_dry_run", to=to, subject=subject)
        return False
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        log.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("email_failed", to=to, error=str(exc))
        return False
