"""Agent 8 — Interview Preparation. Build a prep packet on a positive signal."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.db.models import Application, Interview, Job, Profile

SYSTEM = """You are an interview coach. Produce a JSON prep packet:
{
 "company_research": "concise summary + what they likely value",
 "technical_questions": ["..."],
 "behavioral_questions": ["..."],
 "star_examples": [{"question":"...","situation":"...","task":"...","action":"...","result":"..."}],
 "questions_to_ask": ["..."]
}
Ground STAR examples ONLY in the candidate's real experience. 5-8 items per list."""


class InterviewAgent(BaseAgent):
    name = "interview"

    def run(self, application: Application) -> Interview:
        job = self.db.get(Job, application.job_id)
        profile = self.db.query(Profile).filter(Profile.user_id == application.user_id).one_or_none()
        prompt = (
            f"COMPANY: {job.company}\nROLE: {job.title}\n"
            f"JOB DESCRIPTION:\n{job.description[:3000]}\n\n"
            f"CANDIDATE EXPERIENCE: {profile.experience if profile else []}\n"
            f"SKILLS: {profile.skills if profile else []}"
        )
        packet = self.llm.json(SYSTEM, prompt, max_tokens=1800)
        if not packet:
            packet = {
                "company_research": f"Research {job.company}: product, customers, recent news.",
                "technical_questions": ["Explain a project end-to-end.", "System design basics."],
                "behavioral_questions": ["Tell me about a conflict.", "A failure you learned from."],
                "star_examples": [],
                "questions_to_ask": ["What does success look like in 90 days?"],
            }
        interview = Interview(
            application_id=application.id,
            round_name="prep",
            prep_packet=packet,
        )
        self.db.add(interview)
        self.db.commit()
        self.audit("interview_prep_generated", target=application.id)
        self.log.info("interview_prep_done", app_id=application.id)
        return interview
