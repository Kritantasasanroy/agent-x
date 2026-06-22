"""Out-of-band notifications for events that need a human (e.g. CAPTCHA).

Tries Telegram first (instant, tap from phone), then email, then just logs. All channels
are optional — with nothing configured this degrades to a structured log line, so the
pipeline never breaks. This is the human-in-the-loop hook: when the apply bot hits a
CAPTCHA or an ambiguous form it pings YOU instead of trying to defeat the check.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.email import send_email

log = get_logger("notify")


def _telegram(text: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": settings.telegram_chat_id, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as exc:  # noqa: BLE001
        log.warning("telegram_failed", error=str(exc))
        return False


def notify(title: str, body: str = "", url: str = "") -> bool:
    """Send a notification through the best available channel. Returns True if delivered."""
    text = title if not body else f"{title}\n\n{body}"
    if url:
        text = f"{text}\n{url}"

    if _telegram(text):
        log.info("notify_sent", channel="telegram", title=title)
        return True

    target = settings.notify_email or settings.smtp_from
    if target and send_email(target, f"[JobHunter] {title}", text):
        log.info("notify_sent", channel="email", title=title)
        return True

    log.info("notify_logged", title=title, body=body, url=url)
    return False
