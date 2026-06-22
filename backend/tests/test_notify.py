"""Notifier degrades to a no-op log when nothing is configured (never raises)."""

from __future__ import annotations

from app.services.notify import _telegram, notify


def test_telegram_disabled_without_config():
    assert _telegram("hello") is False


def test_notify_returns_false_when_unconfigured():
    # no telegram, no notify_email/smtp -> logs and returns False, must not raise
    assert notify("Title", "body", "https://example.com/apply") is False


def test_notify_telegram_path(monkeypatch):
    sent = {}

    def fake_post(url, json=None, timeout=None):
        sent["url"] = url
        sent["text"] = json["text"]

        class R:
            status_code = 200

        return R()

    monkeypatch.setattr("app.services.notify.settings.telegram_bot_token", "T", raising=False)
    monkeypatch.setattr("app.services.notify.settings.telegram_chat_id", "C", raising=False)
    monkeypatch.setattr("app.services.notify.httpx.post", fake_post)

    assert notify("CAPTCHA", "Acme job", "https://x/apply") is True
    assert "CAPTCHA" in sent["text"]
    assert "api.telegram.org" in sent["url"]
