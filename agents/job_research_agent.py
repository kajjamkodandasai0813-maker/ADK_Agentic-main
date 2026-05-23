"""
agents/job_research_agent.py - Researches company, role, and market insights
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from tools.search_tools import search_company_info, search_job_market_trends, search_salary_data


class JobResearchAgent(BaseAgent):
    """
    Researches the target company, job role, and market data.
    Provides strategic context to all downstream agents.

    Sub-tasks:
    1. Company research (culture, values, products, interview style)
    2. Job market trends for the domain
    3. Salary benchmarks for negotiation
    4. JD analysis (requirements, must-haves, nice-to-haves)
    """

    def __init__(self):
        super().__init__(
            name="JobResearchAgent",
            description=(
                "You are an expert job market analyst and career strategist. "
                "You analyze job descriptions deeply, research companies thoroughly, "
                "and provide actionable intelligence to help candidates win their dream jobs."
            ),
        )

    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research company, role, and market.

        Input keys used: company_name, job_description, target_role
        Output keys: company_research, salary_data, job_market_data, jd_analysis
        """
        company_name = session_data.get("company_name", "Unknown Company")
        job_description = session_data.get("job_description", "")
        target_role = session_data.get("target_role", "")

        # ── Tool calls ──────────────────────────────────────────────
        company_info = search_company_info(company_name)
        job_trends = search_job_market_trends(self._infer_domain(job_description, target_role))
        salary_info = search_salary_data(target_role or "software engineer", "mid")

        # ── LLM analysis of the JD ──────────────────────────────────
        jd_analysis = self._analyze_jd(job_description, company_name, company_info)

        return {
            "success": True,
            "company_research": company_info,
            "salary_data": salary_info,
            "job_market_data": job_trends,
            "jd_analysis": jd_analysis,
            "agent": self.name,
        }

    def _infer_domain(self, jd: str, role: str) -> str:
        """Infer job domain from JD and role text."""
        combined = (jd + " " + role).lower()
        if any(w in combined for w in ["machine learning", "ai", "deep learning", "llm", "nlp", "data science"]):
            return "ai_ml"
        elif any(w in combined for w in ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "sre"]):
            return "cloud"
        else:
            return "fullstack"

    def _analyze_jd(self, jd: str, company: str, company_info: dict) -> str:
        """Deep analysis of the job description using LLM."""
        company_context = ""
        if company_info.get("found"):
            c = company_info.get("company", {})
            company_context = f"""
Company Culture: {c.get('culture', 'N/A')}
Company Values: {c.get('values', 'N/A')}
Interview Style: {c.get('interview_style', 'N/A')}
"""

        prompt = self._format_prompt(
            self._build_system_context(),
            f"""
Analyze the following job description for {company} and provide actionable intelligence.

JOB DESCRIPTION:
{jd}

{company_context}

Provide a comprehensive analysis including:

## ROLE SUMMARY
[2-3 sentence summary of what this role actually does]

## MUST-HAVE REQUIREMENTS
[Critical qualifications — missing these = auto-reject]

## NICE-TO-HAVE REQUIREMENTS  
[Preferred but not mandatory — having these = advantage]

## KEY RESPONSIBILITIES (ranked by importance)
[Top 5-7 key responsibilities]

## TECHNICAL SKILLS REQUIRED
[Hard technical skills explicitly mentioned]

## SOFT SKILLS REQUIRED
[Communication, leadership, collaboration signals]

## EXPERIENCE LEVEL
[Entry/Mid/Senior based on requirements analysis]

## RED FLAGS or CONCERNS
[Anything unusual, unrealistic, or worth clarifying]

## APPLICATION STRATEGY
[How to position this specific application to win — based on company culture and JD]

## KEYWORDS TO INCLUDE
[Most important ATS keywords extracted from JD]

## QUESTIONS TO ASK INTERVIEWER
[3-5 smart questions to ask based on role and company]
"""
        )

        try:
            return self._call_llm(prompt)
        except Exception as e:
            return f"JD analysis failed: {str(e)}"
