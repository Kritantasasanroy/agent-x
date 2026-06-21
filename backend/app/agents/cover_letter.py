"""Agent 4 — Cover Letter Generator. 250–400 words, personalized + truthful."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.db.models import CoverLetter, Job, Profile
from app.services.documents import render_both

SYSTEM = """You write concise, sincere cover letters (250-400 words).
Reference the specific company, the role, and 1-2 genuinely relevant experiences/projects
from the candidate's background. Do NOT fabricate. Professional, warm, no clichés.
Output the letter text only."""


class CoverLetterAgent(BaseAgent):
    name = "cover_letter"

    def run(self, job: Job, profile: Profile) -> CoverLetter:
        prompt = (
            f"CANDIDATE: {profile.user.full_name if profile.user else ''}\n"
            f"SKILLS: {', '.join(profile.skills or [])}\n"
            f"EXPERIENCE: {profile.experience}\n"
            f"PORTFOLIO: {profile.portfolio_url} | GitHub: {profile.github_url}\n\n"
            f"COMPANY: {job.company}\nROLE: {job.title}\n"
            f"JOB DESCRIPTION:\n{job.description[:3000]}\n\n"
            "Write the cover letter (250-400 words)."
        )
        content = self.llm.chat(SYSTEM, prompt, max_tokens=900)
        if content.startswith("[LLM unavailable"):
            content = (
                f"Dear {job.company} Hiring Team,\n\n"
                f"I am excited to apply for the {job.title} role. My background in "
                f"{', '.join((profile.skills or [])[:5])} aligns well with your needs. "
                "I would welcome the chance to contribute.\n\n"
                f"Best regards,\n{profile.user.full_name if profile.user else ''}"
            )

        name = f"{profile.user_id[:6]}_{job.id[:6]}_cover"
        pdf, docx = render_both(content, name, "cover_letters")
        cover = CoverLetter(
            user_id=profile.user_id,
            job_id=job.id,
            content=content,
            pdf_path=pdf,
            docx_path=docx,
        )
        self.db.add(cover)
        self.db.commit()
        self.audit("cover_letter_generated", target=job.id)
        self.log.info("cover_generated", job_id=job.id)
        return cover
