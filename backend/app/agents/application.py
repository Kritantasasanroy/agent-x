"""Agent 5 — Application Agent.

Drives a real browser with Playwright to fill + submit application forms. Persists
screenshots, the answers it gave, and the confirmation page. If a CAPTCHA / human
verification is detected it STOPS and flags the application for human review — it never
attempts to solve or bypass a CAPTCHA.

Playwright is optional at import time: if it (or a browser) is unavailable the agent
degrades to a dry run and marks the application `needs_review`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.agents.base import BaseAgent
from app.core.config import settings
from app.db.models import Application, ApplicationStatus, Job, Profile, Resume
from app.services import greenhouse_apply
from app.services.notify import notify

CAPTCHA_MARKERS = [
    "captcha", "recaptcha", "hcaptcha", "i'm not a robot", "are you human",
    "verify you are human", "cloudflare", "challenge-platform",
]


class ApplicationAgent(BaseAgent):
    name = "application"

    def _shot_dir(self, app_id: str) -> Path:
        d = settings.storage_path / "screenshots" / app_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def answer_question(self, question: str, profile: Profile, job: Job) -> str:
        """Use the LLM for open-ended application questions, grounded in the profile."""
        system = (
            "Answer this job-application question truthfully and concisely as the candidate. "
            "Use only facts from the provided profile. 2-5 sentences."
        )
        prompt = (
            f"PROFILE skills={profile.skills} exp={profile.experience} "
            f"location={profile.location}\nJOB: {job.title} @ {job.company}\n"
            f"QUESTION: {question}"
        )
        return self.llm.chat(system, prompt, max_tokens=300)

    def run(self, application: Application, auto_submit: bool = True) -> Application:
        job = self.db.get(Job, application.job_id)
        profile = (
            self.db.query(Profile).filter(Profile.user_id == application.user_id).one_or_none()
        )
        resume = self.db.get(Resume, application.resume_id) if application.resume_id else None

        try:
            self._drive(application, job, profile, resume, auto_submit)
        except Exception as exc:  # noqa: BLE001
            application.status = ApplicationStatus.failed
            application.error = str(exc)[:1000]
            self.log.error("application_failed", app_id=application.id, error=str(exc))
        self.db.commit()
        self.audit("application_attempt", target=application.id, status=application.status)
        return application

    # ------------------------------------------------------------------ #
    def _drive(self, application, job, profile, resume, auto_submit) -> None:
        # Preferred path: Greenhouse boards accept a clean API application (no CAPTCHA).
        if job and (job.source == "greenhouse" or greenhouse_apply.gh_ids(job)):
            result = greenhouse_apply.apply(profile, job, resume)
            application.answers = result.fields or {}
            if result.submitted:
                application.status = ApplicationStatus.applied
                application.submitted_at = datetime.now(timezone.utc)
                application.confirmation = "greenhouse_api_ok"
                self.log.info("application_submitted_greenhouse", app_id=application.id)
                return
            if result.dry_run:
                self._needs_review(application, f"greenhouse_dry_run:{result.reason}")
                return
            self._needs_review(application, f"greenhouse_apply_failed:{result.reason}")
            return

        try:
            from playwright.sync_api import sync_playwright
        except Exception:  # noqa: BLE001
            self._needs_review(application, "playwright_unavailable")
            return

        if not job.apply_url:
            self._needs_review(application, "no_apply_url")
            return

        shots = self._shot_dir(application.id)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=settings.playwright_headless)
            except Exception as exc:  # noqa: BLE001
                self._needs_review(application, f"browser_launch_failed:{exc}")
                return
            ctx = browser.new_context(
                storage_state=self._state_path(application.user_id) or None
            )
            page = ctx.new_page()
            page.goto(job.apply_url, wait_until="domcontentloaded", timeout=45000)

            if self._blocking_captcha(page):
                page.screenshot(path=str(shots / "captcha.png"))
                application.screenshots = [str(shots / "captcha.png")]
                # Human-in-the-loop: if running headed with a manual wait, let YOU solve the
                # CAPTCHA in the open window, then continue. We never solve/bypass it ourselves.
                if not self._wait_for_human_captcha(page):
                    self._needs_review(application, "captcha_detected")
                    browser.close()
                    return

            # Best-effort generic form fill (sites vary — extend per ATS).
            answers = self._fill_common_fields(page, profile)
            if resume and resume.pdf_path:
                self._upload_resume(page, resume.pdf_path)

            page.screenshot(path=str(shots / "filled.png"))
            application.screenshots = [str(shots / "filled.png")]
            application.answers = answers

            paused = bool(profile and profile.user and profile.user.automation_paused)
            if not settings.enable_real_apply:
                # Safety gate: form is filled + screenshotted, but we never click submit
                # until you turn on ENABLE_REAL_APPLY. Nothing is sent to the company.
                self._needs_review(application, "dry_run_filled")
            elif auto_submit and not paused:
                submitted = self._submit(page)
                if submitted:
                    page.screenshot(path=str(shots / "confirmation.png"))
                    application.screenshots = application.screenshots + [str(shots / "confirmation.png")]
                    application.confirmation = (page.title() or "")[:255]
                    application.status = ApplicationStatus.applied
                    application.submitted_at = datetime.now(timezone.utc)
                else:
                    self._needs_review(application, "submit_button_not_found")
            else:
                self._needs_review(application, "auto_submit_disabled")

            # persist session for reuse
            ctx.storage_state(path=self._state_path(application.user_id, create=True))
            browser.close()

    def _fill_common_fields(self, page, profile) -> dict:
        answers: dict[str, str] = {}
        mapping = {
            "input[name*=name i]": (profile.user.full_name if profile and profile.user else ""),
            "input[type=email]": (profile.user.email if profile and profile.user else ""),
            "input[name*=phone i]": (profile.phone if profile else ""),
            "input[name*=linkedin i]": (profile.linkedin_url if profile else ""),
            "input[name*=github i]": (profile.github_url if profile else ""),
            "input[name*=location i]": (profile.location if profile else ""),
        }
        for selector, value in mapping.items():
            if not value:
                continue
            try:
                el = page.query_selector(selector)
                if el:
                    el.fill(value)
                    answers[selector] = value
            except Exception:  # noqa: BLE001
                continue
        return answers

    def _upload_resume(self, page, pdf_path: str) -> None:
        try:
            file_input = page.query_selector("input[type=file]")
            if file_input:
                file_input.set_input_files(pdf_path)
        except Exception as exc:  # noqa: BLE001
            self.log.warning("resume_upload_failed", error=str(exc))

    def _submit(self, page) -> bool:
        for selector in (
            "button[type=submit]",
            "input[type=submit]",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
        ):
            try:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    page.wait_for_load_state("networkidle", timeout=20000)
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def _blocking_captcha(self, page) -> bool:
        """True only for an ACTUAL human-verification wall, not a passive/invisible widget.

        Many legit ATS forms (Lever, etc.) embed an invisible reCAPTCHA script — the word
        'recaptcha' in the HTML must NOT block us. We flag a real blocker when the page is an
        interstitial (Cloudflare 'Just a moment', 'Attention Required', access wall) or when
        CAPTCHA markers are present AND there's no fillable form to proceed with.
        """
        interstitial = (
            "just a moment", "attention required", "checking your browser",
            "verify you are human", "access denied", "are you a robot",
        )
        title = (page.title() or "").lower()
        if any(t in title for t in interstitial):
            return True
        content = (page.content() or "").lower()
        if not any(m in content for m in CAPTCHA_MARKERS):
            return False
        # markers present — only blocking if we can't actually fill anything
        try:
            fields = page.query_selector_all("input:not([type=hidden]), textarea, select")
            visible = sum(1 for f in fields if f.is_visible())
        except Exception:  # noqa: BLE001
            visible = 0
        return visible < 2

    def _wait_for_human_captcha(self, page) -> bool:
        """Pause on a CAPTCHA so a human can solve it in a visible browser, then resume.

        Only active when running headed (`PLAYWRIGHT_HEADLESS=false`) with a positive
        `CAPTCHA_MANUAL_WAIT_SECONDS`. Polls until the CAPTCHA markers disappear (you solved
        it) or the wait elapses. Returns True if it cleared. We do NOT solve it ourselves.
        """
        wait = settings.captcha_manual_wait_seconds
        if settings.playwright_headless or wait <= 0:
            return False
        notify(
            "Solve the CAPTCHA in the open browser window",
            body=f"You have ~{wait}s. The bot will continue once it's cleared.",
            url=page.url,
        )
        self.log.info("captcha_waiting_for_human", seconds=wait)
        elapsed = 0
        step = 3
        while elapsed < wait:
            page.wait_for_timeout(step * 1000)
            elapsed += step
            content = (page.content() or "").lower()
            if not any(m in content for m in CAPTCHA_MARKERS):
                self.log.info("captcha_cleared_by_human", elapsed=elapsed)
                return True
        return False

    def _needs_review(self, application: Application, reason: str) -> None:
        application.status = ApplicationStatus.needs_review
        application.needs_review_reason = reason
        self.log.info("application_needs_review", app_id=application.id, reason=reason)
        # Ping the human out-of-band (CAPTCHA/ambiguous form). Never bypass the check.
        if reason.startswith("captcha") or "captcha" in reason:
            try:
                job = self.db.get(Job, application.job_id)
                notify(
                    "Application needs you (CAPTCHA / human check)",
                    body=f"{job.title} @ {job.company}" if job else reason,
                    url=(job.apply_url if job else ""),
                )
            except Exception as exc:  # noqa: BLE001
                self.log.warning("notify_failed", error=str(exc))

    def _state_path(self, user_id: str, create: bool = False) -> str | None:
        d = settings.storage_path / "playwright" / user_id
        if create:
            d.mkdir(parents=True, exist_ok=True)
        f = d / "state.json"
        return str(f) if (create or f.exists()) else None
