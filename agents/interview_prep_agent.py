"""
agents/interview_prep_agent.py - Generates comprehensive interview preparation material
"""

from typing import Any, Dict
from .base_agent import BaseAgent


class InterviewPrepAgent(BaseAgent):
    """
    Generates comprehensive interview preparation including:
    - Behavioral questions with STAR-format sample answers
    - Technical questions specific to the role
    - Situational questions
    - Culture-fit questions
    - Questions to ask the interviewer
    - Salary negotiation strategy
    """

    def __init__(self):
        super().__init__(
            name="InterviewPrepAgent",
            description=(
                "You are a world-class interview coach who has helped hundreds of candidates "
                "land jobs at top companies. You create highly personalized, role-specific interview "
                "preparation materials using the STAR framework for behavioral questions. "
                "You focus on practical, honest preparation — not generic advice."
            ),
        )

    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete interview preparation material.

        Input keys used: parsed_resume, job_description, company_name,
                         company_research, jd_analysis, salary_data, target_role
        Output keys: interview_prep
        """
        parsed_resume = session_data.get("parsed_resume", "")
        job_description = session_data.get("job_description", "")
        company_name = session_data.get("company_name", "the company")
        target_role = session_data.get("target_role", "the role")
        company_research = session_data.get("company_research", {})
        jd_analysis = session_data.get("jd_analysis", "")
        salary_data = session_data.get("salary_data", {})

        # Extract company interview style
        interview_style = ""
        company_values = ""
        if company_research.get("found"):
            c = company_research.get("company", {})
            interview_style = c.get("interview_style", "")
            company_values = str(c.get("values", ""))

        # Extract salary range for negotiation tips
        salary_range = salary_data.get("salary_range", {})
        salary_min = salary_range.get("min", "research required")
        salary_max = salary_range.get("max", "research required")
        negotiation_tips = salary_data.get("negotiation_tips", [])

        prompt = self._format_prompt(
            self._build_system_context(),
            f"""
Generate comprehensive interview preparation for this specific role and company.

═══════════════════════════════════════════
TARGET ROLE: {target_role} at {company_name}
═══════════════════════════════════════════

CANDIDATE BACKGROUND:
{str(parsed_resume)[:2000] if parsed_resume else 'Senior professional with relevant experience'}

JOB DESCRIPTION:
{job_description}

JD KEY REQUIREMENTS:
{jd_analysis[:1500] if jd_analysis else 'Analyze from JD above'}

COMPANY INTERVIEW STYLE: {interview_style or 'Standard behavioral + technical format'}
COMPANY VALUES: {company_values or 'Research company values'}

═══════════════════════════════════════════
Generate ALL of the following sections:
═══════════════════════════════════════════

## 1. ROLE OVERVIEW FOR INTERVIEW
[Brief 3-sentence framing of what this role is really about — helps candidate internalize the job]

## 2. YOUR ELEVATOR PITCH (for "Tell me about yourself")
[Write a 60-second, role-specific elevator pitch for this candidate]

## 3. BEHAVIORAL QUESTIONS (STAR Format)
[Generate 6 behavioral questions most likely for this role]
For each question:
**Q: [Question]**
*Why they ask this:* [Brief explanation]
*STAR Sample Answer:*
- Situation: [Context setup]
- Task: [What was needed]
- Action: [What candidate did]
- Result: [Quantified outcome]

## 4. TECHNICAL QUESTIONS
[5-7 technical questions specific to the role's tech stack and requirements]
For each:
**Q: [Technical question]**
*Key points to cover:* [What an ideal answer includes]

## 5. SITUATIONAL / CASE QUESTIONS
[3-4 situational questions for this role]
**Q: [Question]**
*Approach:* [How to structure the answer]

## 6. CULTURE FIT QUESTIONS
[3-4 company-specific culture fit questions]
**Q: [Question]**
*How to align with {company_name}'s values:* [Specific guidance]

## 7. QUESTIONS TO ASK THE INTERVIEWER
[8 smart, role-specific questions to ask — shows depth of preparation]
Organized by: Role Questions | Team Questions | Company Direction Questions

## 8. COMMON MISTAKES TO AVOID
[5 specific mistakes candidates make in interviews for this TYPE of role]

## 9. SALARY NEGOTIATION STRATEGY
Market Range for {target_role}: ${salary_min:,} - ${salary_max:,}
[Specific negotiation script and strategy for {company_name}]
Tips: {' | '.join(negotiation_tips[:3]) if negotiation_tips else 'Research market rates, always negotiate, anchor high'}

## 10. 7-DAY INTERVIEW PREP PLAN
[Day-by-day action plan to prepare for this interview]

## 11. TOP 3 THINGS THAT WILL WIN THIS INTERVIEW
[The most critical factors specific to this role and company]
"""
        )

        try:
            result = self._call_llm(prompt)
            return {
                "success": True,
                "interview_prep": result,
                "agent": self.name,
                "sections": self._count_sections(result),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interview_prep": "",
                "agent": self.name,
            }

    def _count_sections(self, content: str) -> int:
        """Count number of sections in the prep content."""
        return content.count("## ")
