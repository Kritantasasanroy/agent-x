"""Agent 3 — Resume Optimization. Tailor the master resume to a job.

Hard rule: NEVER invent experience. Only reorder / rephrase / emphasize / keyword-optimize
the facts already present in the master resume.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.db.models import CoverLetter, Job, Profile, Resume  # noqa: F401
from app.services.documents import render_both

SYSTEM = """You are an expert ATS resume writer.
STRICT RULES:
- Use ONLY facts present in the master resume. Never invent employers, titles, dates,
  degrees, or skills the candidate does not have.
- You MAY reorder sections, rephrase bullets, surface relevant projects, and weave in
  keywords from the job that the candidate genuinely matches.
- Keep it truthful, concise, one-to-two pages, ATS-friendly plain text.
Output plain text resume only. Use UPPERCASE section headers (e.g. EXPERIENCE)."""


class ResumeAgent(BaseAgent):
    name = "resume"

    def run(self, job: Job, profile: Profile, variant: str = "A") -> Resume:
        prompt = (
            f"MASTER RESUME:\n{profile.master_resume}\n\n"
            f"CANDIDATE SKILLS: {', '.join(profile.skills or [])}\n\n"
            f"TARGET JOB: {job.title} at {job.company}\n"
            f"JOB DESCRIPTION:\n{job.description[:4000]}\n\n"
            f"Required keywords to surface where truthful: {', '.join(job.required_skills or [])}\n"
            f"Produce a tailored resume for variant {variant}. "
            f"Variant A=impact-first, B=skills-first, C=projects-first."
        )
        content = self.llm.chat(SYSTEM, prompt, max_tokens=2000)
        if content.startswith("[LLM unavailable"):
            content = self._fallback_resume(job, profile)

        version = (
            self.db.query(Resume)
            .filter(Resume.user_id == profile.user_id, Resume.job_id == job.id)
            .count()
            + 1
        )
        name = f"{profile.user_id[:6]}_{job.id[:6]}_v{version}{variant}"
        pdf, docx = render_both(content, name, "resumes")
        resume = Resume(
            user_id=profile.user_id,
            job_id=job.id,
            variant=variant,
            version=version,
            content=content,
            keywords=job.required_skills or [],
            pdf_path=pdf,
            docx_path=docx,
        )
        self.db.add(resume)
        self.db.commit()
        self.audit("resume_generated", target=job.id, variant=variant, version=version)
        self.log.info("resume_generated", job_id=job.id, variant=variant)
        return resume

    def _fallback_resume(self, job: Job, profile: Profile) -> str:
        return (
            f"{profile.user.full_name if profile.user else ''}\n"
            f"{profile.location} | {profile.linkedin_url} | {profile.github_url}\n\n"
            "SUMMARY\n"
            f"Candidate targeting {job.title} at {job.company}.\n\n"
            "SKILLS\n"
            f"{', '.join(profile.skills or [])}\n\n"
            "EXPERIENCE\n"
            + "\n".join(
                f"- {e.get('title','')} @ {e.get('company','')} ({e.get('dates','')})"
                for e in (profile.experience or [])
            )
            + "\n\nMASTER RESUME (verbatim)\n"
            + profile.master_resume
        )
