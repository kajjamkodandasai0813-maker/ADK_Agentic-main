"""
agents/resume_parser_agent.py - Parses and structures resume information
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class ResumeParserAgent(BaseAgent):
    """
    Parses raw resume text and extracts structured information.
    Output feeds into all downstream agents.
    """

    def __init__(self):
        super().__init__(
            name="ResumeParserAgent",
            description=(
                "You are an expert resume analyst with 15+ years of recruiting experience. "
                "You extract structured, accurate information from resumes with zero hallucination. "
                "You only report what is explicitly stated in the resume."
            ),
        )

    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the resume and return structured data.

        Input keys used: raw_resume
        Output keys: parsed_resume (structured dict)
        """
        raw_resume = session_data.get("raw_resume", "")
        if not raw_resume:
            return {"success": False, "error": "No resume text provided", "parsed_resume": {}}

        prompt = self._format_prompt(
            self._build_system_context(),
            f"""
You are given the following resume. Extract all information into a structured format.

RESUME TEXT:
{raw_resume}

Extract and return the following fields in a structured markdown format:

## APPLICANT PROFILE
- Full Name:
- Email:
- Phone:
- Location:
- LinkedIn:
- GitHub/Portfolio:

## PROFESSIONAL SUMMARY
[2-3 sentence summary of the candidate]

## YEARS OF EXPERIENCE
[Total estimated years of professional experience]

## TECHNICAL SKILLS
[List all technical skills, tools, programming languages, frameworks, cloud platforms]

## SOFT SKILLS
[List soft skills mentioned or implied]

## WORK EXPERIENCE
[For each role - Company | Title | Duration | Key achievements (bullet points)]

## EDUCATION
[Degree | Institution | Year | GPA if mentioned]

## CERTIFICATIONS
[List all certifications with issuer and date]

## PROJECTS
[Project name | Tech stack | Key impact]

## KEY ACHIEVEMENTS
[Top 5 quantified achievements from the entire resume]

## CAREER LEVEL ASSESSMENT
[Entry / Mid / Senior / Staff / Manager — with reasoning]

## STRENGTHS
[Top 3 strengths based on the resume]

## GAPS / WEAKNESSES
[Any notable gaps or areas that might need strengthening]

Be precise. Only use information explicitly present in the resume.
"""
        )

        try:
            result = self._call_llm(prompt)
            return {
                "success": True,
                "parsed_resume": result,
                "agent": self.name,
                "raw_resume_length": len(raw_resume),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "parsed_resume": "",
                "agent": self.name,
            }
