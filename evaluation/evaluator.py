"""
evaluation/evaluator.py - Master evaluator that orchestrates all evaluation modules
"""

import json
from datetime import datetime
from typing import Optional
from config import EVALUATION_CONFIG
from .resume_evaluator import ResumeEvaluator
from .cover_letter_evaluator import CoverLetterEvaluator
from .metrics import EvaluationReport, EvaluationMetrics


class MasterEvaluator:
    """
    Master evaluation orchestrator.
    Evaluates all pipeline outputs and generates a consolidated report.

    Evaluates:
    - Tailored Resume vs. Job Description
    - Cover Letter quality and personalization
    - Interview Prep coverage and depth
    """

    def __init__(self):
        self.resume_evaluator = ResumeEvaluator()
        self.cover_letter_evaluator = CoverLetterEvaluator()
        self.metrics = EvaluationMetrics()
        self.evaluation_history = []

    def evaluate_resume(self, tailored_resume: str, job_description: str) -> EvaluationReport:
        """Evaluate the tailored resume against the job description."""
        report = self.resume_evaluator.evaluate(tailored_resume, job_description)
        self.evaluation_history.append(report)
        return report

    def evaluate_cover_letter(
        self, cover_letter: str, job_description: str, company_name: str
    ) -> EvaluationReport:
        """Evaluate the cover letter for quality and personalization."""
        report = self.cover_letter_evaluator.evaluate(cover_letter, job_description, company_name)
        self.evaluation_history.append(report)
        return report

    def evaluate_interview_prep(self, interview_content: str, job_description: str) -> EvaluationReport:
        """
        Evaluate interview preparation content for coverage and depth.
        Uses keyword-based analysis since LLM-generated Q&A is evaluated heuristically.
        """
        from .metrics import ScoreDimension

        config = EVALUATION_CONFIG["interview_prep"]
        dimensions = []
        strengths = []
        improvements = []
        recommendations = []

        content_lower = interview_content.lower()
        word_count = self.metrics.count_words(interview_content)

        # ── Dimension 1: Question Relevance (40%) ─────────────────
        jd_keywords = self.metrics.extract_keywords(job_description)[:25]
        relevance_score = self.metrics.keyword_overlap_score(interview_content, jd_keywords)
        dimensions.append(ScoreDimension(
            name="Question Relevance",
            score=relevance_score,
            weight=config["question_relevance_weight"],
            details=f"{int(relevance_score * len(jd_keywords) / 100)}/{len(jd_keywords)} JD topics covered",
            passed=relevance_score >= 50,
        ))
        if relevance_score >= 70:
            strengths.append("Interview questions directly address JD requirements")
        else:
            improvements.append("Add more role-specific questions matching JD requirements")

        # ── Dimension 2: Answer Quality (40%) ─────────────────────
        answer_score = self._score_answer_quality(interview_content)
        dimensions.append(ScoreDimension(
            name="Answer Quality",
            score=answer_score,
            weight=config["answer_quality_weight"],
            details="STAR format, specificity, and concrete examples",
            passed=answer_score >= 60,
        ))

        star_signals = ["situation", "task", "action", "result", "star"]
        star_found = sum(1 for s in star_signals if s in content_lower)
        if star_found >= 3:
            strengths.append("Uses STAR format for behavioral answers")
        else:
            improvements.append("Structure behavioral answers using STAR (Situation, Task, Action, Result)")

        # ── Dimension 3: Coverage (20%) ────────────────────────────
        question_count = content_lower.count("?")
        coverage_score = min((question_count / 15) * 100, 100)  # Target: 15+ Qs
        dimensions.append(ScoreDimension(
            name="Coverage Breadth",
            score=coverage_score,
            weight=config["coverage_weight"],
            details=f"{question_count} questions generated (target: 15+)",
            passed=question_count >= 10,
        ))

        if question_count >= 15:
            strengths.append(f"Comprehensive coverage with {question_count} interview questions")
        elif question_count < 8:
            improvements.append(f"Only {question_count} questions — generate at least 15 for thorough prep")

        # ── Interview categories coverage ──────────────────────────
        categories = {
            "behavioral": ["tell me about", "describe a time", "give an example", "how did you"],
            "technical": ["how would you", "explain", "what is", "design a"],
            "situational": ["what would you", "how would you handle", "imagine"],
            "culture_fit": ["why this company", "why do you want", "what motivates", "career goals"],
        }
        covered = [cat for cat, signals in categories.items()
                   if any(s in content_lower for s in signals)]
        if len(covered) >= 3:
            strengths.append(f"Covers {len(covered)}/4 interview types: {', '.join(covered)}")
        else:
            missing = [c for c in categories if c not in covered]
            improvements.append(f"Missing question types: {', '.join(missing)}")

        # ── Final Score ────────────────────────────────────────────
        overall = self.metrics.calculate_weighted_score(dimensions)
        grade = EvaluationMetrics.score_to_grade(overall)
        passed = overall >= config["pass_threshold"]

        recommendations.append("Practice answers out loud — silent reading vs. speaking reveals gaps")
        recommendations.append("Record yourself answering and review for filler words and pacing")
        if overall >= 80:
            recommendations.insert(0, "Excellent prep material. Practice 3x and you'll be ready!")

        report = EvaluationReport(
            artifact_type="interview_prep",
            overall_score=overall,
            grade=grade,
            passed=passed,
            threshold=config["pass_threshold"],
            dimensions=dimensions,
            strengths=strengths,
            improvements=improvements,
            recommendations=recommendations,
            metadata={"question_count": question_count, "word_count": word_count},
        )
        self.evaluation_history.append(report)
        return report

    def _score_answer_quality(self, content: str) -> float:
        """Heuristic scoring of answer quality."""
        score = 40.0
        content_lower = content.lower()

        # STAR signals
        star_signals = ["situation", "task", "action", "result", "outcome"]
        score += sum(5 for s in star_signals if s in content_lower)

        # Quantified results
        import re
        quantified = len(re.findall(r'\d+%|\$\d+|\d+x|\d+\s+(people|users|engineers|weeks|months)', content))
        score += min(quantified * 4, 20)

        # Specificity signals
        specificity = ["specifically", "for example", "in particular", "such as", "for instance"]
        score += sum(3 for s in specificity if s in content_lower)

        return max(0.0, min(100.0, score))

    def generate_master_report(
        self,
        resume_report: EvaluationReport,
        cover_letter_report: EvaluationReport,
        interview_report: EvaluationReport,
        user_info: dict = None,
    ) -> str:
        """
        Generate a consolidated master evaluation report as formatted text.

        Args:
            resume_report: Resume evaluation result
            cover_letter_report: Cover letter evaluation result
            interview_report: Interview prep evaluation result
            user_info: Optional dict with applicant/job metadata

        Returns:
            Formatted master report string
        """
        avg_score = (
            resume_report.overall_score
            + cover_letter_report.overall_score
            + interview_report.overall_score
        ) / 3

        all_passed = all(
            r.passed for r in [resume_report, cover_letter_report, interview_report]
        )

        report_lines = [
            "=" * 70,
            "     JOB APPLICATION MASTER EVALUATION REPORT",
            "=" * 70,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if user_info:
            report_lines += [
                f"Applicant : {user_info.get('name', 'N/A')}",
                f"Role      : {user_info.get('role', 'N/A')}",
                f"Company   : {user_info.get('company', 'N/A')}",
            ]

        report_lines += [
            "",
            "─" * 70,
            "OVERALL APPLICATION SCORE",
            "─" * 70,
            f"  Average Score  : {avg_score:.1f}/100  [{EvaluationMetrics.score_to_grade(avg_score)}]",
            f"  Application    : {'✓ READY TO SUBMIT' if all_passed else '✗ NEEDS IMPROVEMENT'}",
            "",
            "  Component Scores:",
            f"    Resume       : {resume_report.overall_score:.1f}/100  [{resume_report.grade}]  {'✓' if resume_report.passed else '✗'}",
            f"    Cover Letter : {cover_letter_report.overall_score:.1f}/100  [{cover_letter_report.grade}]  {'✓' if cover_letter_report.passed else '✗'}",
            f"    Interview    : {interview_report.overall_score:.1f}/100  [{interview_report.grade}]  {'✓' if interview_report.passed else '✗'}",
            "",
            "─" * 70,
        ]

        # Append individual reports
        for report in [resume_report, cover_letter_report, interview_report]:
            report_lines.append(report.to_text())
            report_lines.append("")

        # Top 5 action items across all reports
        all_improvements = (
            resume_report.improvements
            + cover_letter_report.improvements
            + interview_report.improvements
        )
        if all_improvements:
            report_lines += [
                "─" * 70,
                "TOP PRIORITY ACTIONS",
                "─" * 70,
            ]
            for i, item in enumerate(all_improvements[:5], 1):
                report_lines.append(f"  {i}. {item}")

        report_lines.append("=" * 70)
        return "\n".join(report_lines)

    def get_evaluation_summary(self) -> dict:
        """Return a summary of all evaluations done in this session."""
        return {
            "total_evaluations": len(self.evaluation_history),
            "reports": [r.to_dict() for r in self.evaluation_history],
            "average_score": (
                sum(r.overall_score for r in self.evaluation_history) / len(self.evaluation_history)
                if self.evaluation_history else 0
            ),
            "all_passed": all(r.passed for r in self.evaluation_history),
        }
