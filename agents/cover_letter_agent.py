"""
agents/cover_letter_agent.py - Writes a personalized, compelling cover letter
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class CoverLetterAgent(BaseAgent):
    """
    Writes a personalized cover letter that:
    - Opens with a compelling hook
    - Connects candidate's top 2-3 achievements to role requirements
    - Shows genuine company research and enthusiasm
    - Closes with a confident call to action
    - Avoids generic, overused phrases
    """

    def __init__(self):
        super().__init__(
            name="CoverLetterAgent",
            description=(
                "You are an expert career coach and professional writer specializing in job applications. "
                "You write cover letters that get candidates interviews. Your letters are concise (250-320 words), "
                "personalized, achievement-focused, and never generic. "
                "You never start with 'I am writing to express my interest' or similar clichés."
            ),
        )

    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write a tailored cover letter.

        Input keys used: parsed_resume, job_description, company_name,
                         company_research, jd_analysis, target_role, applicant_name
        Output keys: cover_letter
        """
        parsed_resume = session_data.get("parsed_resume", "")
        job_description = session_data.get("job_description", "")
        company_name = session_data.get("company_name", "the company")
        target_role = session_data.get("target_role", "the role")
        applicant_name = session_data.get("applicant_name", "Applicant")
        company_research = session_data.get("company_research", {})
        jd_analysis = session_data.get("jd_analysis", "")

        # Extract company insights for personalization
        company_culture = ""
        company_mission = ""
        if company_research.get("found"):
            c = company_research.get("company", {})
            company_culture = c.get("culture", "")
            company_mission = c.get("mission", "")

        prompt = self._format_prompt(
            self._build_system_context(),
            f"""
Write a compelling, personalized cover letter for the following application.

═══════════════════════════════════════════
APPLICANT INFORMATION:
═══════════════════════════════════════════
Name: {applicant_name}
Resume Summary: {str(parsed_resume)[:2000] if parsed_resume else 'Not available'}

═══════════════════════════════════════════
TARGET ROLE: {target_role}
COMPANY: {company_name}
═══════════════════════════════════════════
Company Mission: {company_mission or 'Research and reference the company mission'}
Company Culture: {company_culture or 'Research and reference the company culture'}

═══════════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════════
{job_description}

═══════════════════════════════════════════
JD KEY REQUIREMENTS (use for alignment):
═══════════════════════════════════════════
{jd_analysis[:1500] if jd_analysis else 'Analyze the JD above'}

═══════════════════════════════════════════
COVER LETTER REQUIREMENTS:
═══════════════════════════════════════════

STRUCTURE (4 paragraphs, 250-320 words total):

PARAGRAPH 1 — HOOK (2-3 sentences):
• Start with something specific about the company or role
• Show you've done your homework (reference company mission/product/culture)
• State your core value proposition immediately
• NEVER start with "I am writing to express my interest..."

PARAGRAPH 2 — TOP ACHIEVEMENT (3-4 sentences):
• Lead with your most relevant achievement for THIS role
• Must be specific and quantified (numbers, % impact, scale)
• Connect it directly to a key JD requirement

PARAGRAPH 3 — SKILLS + COMPANY FIT (3-4 sentences):
• Highlight 2nd most relevant skill/achievement
• Show cultural fit with the specific company
• Reference something unique about the company that excites you

PARAGRAPH 4 — CALL TO ACTION (2-3 sentences):
• Express enthusiasm without desperation
• Clear, confident call to action
• Professional closing

FORMAT:
[Date]

Dear [Hiring Manager / Specific Name if known],

[Body - 4 paragraphs]

Sincerely,
{applicant_name}
[Contact Info]

RULES:
✓ Use specific numbers and metrics from the applicant's background
✓ Mirror key phrases from the job description naturally
✓ Mention {company_name} by name at least twice
✓ Keep it to 250-320 words in the body
✗ No generic phrases: "passionate", "team player", "hardworking", "quick learner"
✗ No clichéd openers
✗ No fabricated experience
"""
        )

        try:
            result = self._call_llm(prompt)
            return {
                "success": True,
                "cover_letter": result,
                "agent": self.name,
                "word_count_estimate": len(result.split()),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cover_letter": "",
                "agent": self.name,
            }
