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
                browser = p.chromium.launch(headless=True)
            except Exception as exc:  # noqa: BLE001
                self._needs_review(application, f"browser_launch_failed:{exc}")
                return
            ctx = browser.new_context(
                storage_state=self._state_path(application.user_id) or None
            )
            page = ctx.new_page()
            page.goto(job.apply_url, wait_until="domcontentloaded", timeout=45000)

            content = (page.content() or "").lower()
            if any(m in content for m in CAPTCHA_MARKERS):
                page.screenshot(path=str(shots / "captcha.png"))
                application.screenshots = [str(shots / "captcha.png")]
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

            if auto_submit and not (profile and profile.user and profile.user.automation_paused):
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

    def _needs_review(self, application: Application, reason: str) -> None:
        application.status = ApplicationStatus.needs_review
        application.needs_review_reason = reason
        self.log.info("application_needs_review", app_id=application.id, reason=reason)

    def _state_path(self, user_id: str, create: bool = False) -> str | None:
        d = settings.storage_path / "playwright" / user_id
        if create:
            d.mkdir(parents=True, exist_ok=True)
        f = d / "state.json"
        return str(f) if (create or f.exists()) else None
