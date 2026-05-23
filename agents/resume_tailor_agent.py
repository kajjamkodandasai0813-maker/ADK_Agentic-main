"""
agents/resume_tailor_agent.py - Tailors resume to match the specific job description
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class ResumeTailorAgent(BaseAgent):
    """
    Tailors the candidate's resume to maximally align with the target job description.

    Strategy:
    - Mirror JD language and keywords (ATS optimization)
    - Reorder/reweight experience based on role requirements
    - Strengthen impact statements with quantified results
    - Ensure career narrative aligns with role requirements
    """

    def __init__(self):
        super().__init__(
            name="ResumeTailorAgent",
            description=(
                "You are a world-class resume writer and ATS optimization expert. "
                "You tailor resumes to specific job descriptions without fabricating experience. "
                "You reframe real experience using JD language to maximize keyword match and impact. "
                "You NEVER add skills or experiences the candidate doesn't have."
            ),
        )

    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tailor the resume to the job description.

        Input keys used: raw_resume, parsed_resume, job_description, jd_analysis, company_research
        Output keys: tailored_resume
        """
        raw_resume = session_data.get("raw_resume", "")
        parsed_resume = session_data.get("parsed_resume", "")
        job_description = session_data.get("job_description", "")
        jd_analysis = session_data.get("jd_analysis", "")
        company_name = session_data.get("company_name", "the company")

        if not raw_resume or not job_description:
            return {
                "success": False,
                "error": "Missing resume or job description",
                "tailored_resume": "",
            }

        prompt = self._format_prompt(
            self._build_system_context(),
            f"""
Your task is to tailor the following resume for the specific job at {company_name}.

═══════════════════════════════════════════
ORIGINAL RESUME:
═══════════════════════════════════════════
{raw_resume}

═══════════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════════
{job_description}

═══════════════════════════════════════════
JD ANALYSIS (use this for strategy):
═══════════════════════════════════════════
{jd_analysis[:2000] if jd_analysis else 'Not available'}

═══════════════════════════════════════════
TAILORING INSTRUCTIONS:
═══════════════════════════════════════════

1. KEYWORDS: Naturally incorporate must-have keywords from the JD throughout the resume
2. SUMMARY: Rewrite the summary to directly address this specific role and company
3. EXPERIENCE: Reorder bullet points to lead with most relevant achievements
4. IMPACT: Strengthen weak bullet points with stronger action verbs and metrics
5. SKILLS: Reorganize skills section to lead with JD-required skills
6. ATS: Mirror exact terminology from the JD (e.g., if JD says "ML pipelines", use that phrase)
7. HONESTY: Only use skills and experiences already present in the original resume

Return the complete tailored resume in this exact format:

─────────────────────────────────────────
[APPLICANT NAME]
[Email] | [Phone] | [Location] | [LinkedIn] | [GitHub]
─────────────────────────────────────────

PROFESSIONAL SUMMARY
[3-4 sentences tailored to this specific role]

TECHNICAL SKILLS
[Reorganized by JD relevance]

PROFESSIONAL EXPERIENCE

[Company Name] | [Role Title] | [Dates]
• [Achievement bullet 1 — quantified, strong verb]
• [Achievement bullet 2 — quantified, strong verb]
• [Achievement bullet 3 — quantified, strong verb]

[Continue for all roles...]

EDUCATION
[Degree | Institution | Year]

CERTIFICATIONS
[If applicable]

PROJECTS (if applicable)
[Relevant projects]
─────────────────────────────────────────

After the resume, add a section:

## CHANGES MADE
[List the key changes made to optimize for this role]

## ATS KEYWORDS ADDED
[List of JD keywords you've incorporated]
"""
        )

        try:
            result = self._call_llm(prompt)
            # Split off the tailored resume from the changes section
            if "## CHANGES MADE" in result:
                parts = result.split("## CHANGES MADE")
                tailored_resume = parts[0].strip()
                changes_summary = "## CHANGES MADE" + parts[1] if len(parts) > 1 else ""
            else:
                tailored_resume = result
                changes_summary = ""

            return {
                "success": True,
                "tailored_resume": tailored_resume,
                "changes_summary": changes_summary,
                "agent": self.name,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tailored_resume": raw_resume,  # Fallback to original
                "agent": self.name,
            }
