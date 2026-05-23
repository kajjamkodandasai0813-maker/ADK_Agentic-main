"""
evaluation/resume_evaluator.py - Scores tailored resume against job description
"""

import re
from typing import List
from config import EVALUATION_CONFIG
from .metrics import EvaluationMetrics, EvaluationReport, ScoreDimension


class ResumeEvaluator:
    """
    Evaluates how well a tailored resume matches a job description.

    Scoring Dimensions:
    1. Keyword Match    (40%) — JD keywords present in resume
    2. Skills Alignment (30%) — technical/soft skills coverage
    3. Experience Fit   (20%) — experience level signals
    4. Format Quality   (10%) — length, structure, action verbs
    """

    # Strong resume action verbs
    ACTION_VERBS = [
        "led", "built", "designed", "developed", "implemented", "delivered",
        "achieved", "increased", "reduced", "improved", "managed", "launched",
        "created", "engineered", "architected", "optimized", "scaled", "drove",
        "established", "collaborated", "mentored", "automated", "deployed",
        "analyzed", "resolved", "accelerated", "transformed", "spearheaded",
    ]

    # Common skill categories
    TECHNICAL_SKILLS = [
        "python", "java", "javascript", "typescript", "sql", "nosql",
        "react", "node", "aws", "azure", "gcp", "docker", "kubernetes",
        "tensorflow", "pytorch", "machine learning", "deep learning",
        "api", "rest", "graphql", "microservices", "ci/cd", "git",
        "data", "analytics", "statistics", "excel", "tableau", "power bi",
    ]

    def __init__(self):
        self.config = EVALUATION_CONFIG["resume_match"]
        self.metrics = EvaluationMetrics()

    def evaluate(self, tailored_resume: str, job_description: str) -> EvaluationReport:
        """
        Evaluate how well the tailored resume matches the job description.

        Args:
            tailored_resume: The tailored resume text
            job_description: The target job description text

        Returns:
            EvaluationReport with scores, strengths, and improvements
        """
        dimensions = []
        strengths = []
        improvements = []
        recommendations = []

        # ── Dimension 1: Keyword Match (40%) ──────────────────────
        jd_keywords = self.metrics.extract_keywords(job_description)
        unique_keywords = list(set(jd_keywords))[:50]  # Top 50 unique keywords
        keyword_score = self.metrics.keyword_overlap_score(tailored_resume, unique_keywords)

        keyword_dim = ScoreDimension(
            name="Keyword Match",
            score=keyword_score,
            weight=self.config["keyword_weight"],
            details=f"{int(keyword_score * len(unique_keywords) / 100)}/{len(unique_keywords)} JD keywords found",
            passed=keyword_score >= 50,
        )
        dimensions.append(keyword_dim)

        if keyword_score >= 75:
            strengths.append(f"Strong keyword alignment with JD ({keyword_score:.0f}% match)")
        elif keyword_score >= 50:
            improvements.append("Add more JD-specific keywords to improve ATS score")
        else:
            improvements.append(f"Critical: Only {keyword_score:.0f}% keyword overlap — mirror JD language closely")
            recommendations.append("Use exact phrases from the job description in your resume")

        # ── Dimension 2: Skills Alignment (30%) ───────────────────
        skills_in_jd = [s for s in self.TECHNICAL_SKILLS if s in job_description.lower()]
        if skills_in_jd:
            skills_score = self.metrics.keyword_overlap_score(tailored_resume, skills_in_jd)
        else:
            skills_score = 70.0  # No specific skills listed = neutral score

        skills_dim = ScoreDimension(
            name="Skills Alignment",
            score=skills_score,
            weight=self.config["skills_weight"],
            details=f"{len(skills_in_jd)} required skills identified in JD",
            passed=skills_score >= 50,
        )
        dimensions.append(skills_dim)

        if skills_score >= 80:
            strengths.append("Excellent technical skills coverage")
        elif skills_score < 50:
            missing = [s for s in skills_in_jd if s not in tailored_resume.lower()][:5]
            improvements.append(f"Missing key skills: {', '.join(missing)}")

        # ── Dimension 3: Experience Fit (20%) ─────────────────────
        exp_score = self._score_experience_fit(tailored_resume, job_description)
        exp_dim = ScoreDimension(
            name="Experience Fit",
            score=exp_score,
            weight=self.config["experience_weight"],
            details="Based on level indicators and quantified achievements",
            passed=exp_score >= 50,
        )
        dimensions.append(exp_dim)

        quantified = len(re.findall(r'\d+%|\$\d+|\d+x|\d+\s+years?', tailored_resume))
        if quantified >= 5:
            strengths.append(f"Strong use of quantified achievements ({quantified} instances)")
        elif quantified < 2:
            improvements.append("Add numbers/metrics to achievements (%, $, time saved, scale)")
            recommendations.append('Example: "Reduced latency by 40%" instead of "Improved performance"')

        # ── Dimension 4: Format Quality (10%) ─────────────────────
        format_score = self._score_format(tailored_resume)
        format_dim = ScoreDimension(
            name="Format Quality",
            score=format_score,
            weight=self.config["format_weight"],
            details="Length, structure, action verbs, readability",
            passed=format_score >= 60,
        )
        dimensions.append(format_dim)

        word_count = self.metrics.count_words(tailored_resume)
        if word_count < 200:
            improvements.append(f"Resume too short ({word_count} words). Aim for 400-700 words.")
        elif word_count > 1000:
            improvements.append(f"Resume too long ({word_count} words). Keep under 700 words for 1-page.")

        # ── Final Score ────────────────────────────────────────────
        overall = self.metrics.calculate_weighted_score(dimensions)
        grade = EvaluationMetrics.score_to_grade(overall)
        passed = overall >= self.config["pass_threshold"]

        if not recommendations:
            if overall >= 85:
                recommendations.append("Resume is well-optimized. Submit with confidence!")
            else:
                recommendations.append("Review JD once more and mirror its exact language patterns")

        return EvaluationReport(
            artifact_type="resume",
            overall_score=overall,
            grade=grade,
            passed=passed,
            threshold=self.config["pass_threshold"],
            dimensions=dimensions,
            strengths=strengths,
            improvements=improvements,
            recommendations=recommendations,
            metadata={
                "word_count": word_count,
                "quantified_achievements": quantified,
                "jd_keyword_count": len(unique_keywords),
            },
        )

    def _score_experience_fit(self, resume: str, jd: str) -> float:
        """Score experience fit based on level indicators and achievements."""
        score = 60.0  # Base score

        # Quantified achievements boost
        quantified = len(re.findall(r'\d+%|\$\d+|\d+x|\d+\s+years?', resume))
        score += min(quantified * 3, 20)

        # Action verbs boost
        action_count = sum(1 for v in self.ACTION_VERBS if v in resume.lower())
        score += min(action_count * 2, 15)

        # Penalize if experience level mismatch
        senior_signals = ["senior", "lead", "principal", "staff", "architect", "manager"]
        jd_is_senior = any(s in jd.lower() for s in senior_signals)
        resume_has_senior = any(s in resume.lower() for s in senior_signals)

        if jd_is_senior and not resume_has_senior:
            score -= 15

        return max(0.0, min(100.0, score))

    def _score_format(self, resume: str) -> float:
        """Score resume based on formatting quality signals."""
        score = 50.0

        # Word count check
        word_count = self.metrics.count_words(resume)
        if 300 <= word_count <= 700:
            score += 20
        elif 200 <= word_count < 300 or 700 < word_count <= 900:
            score += 10

        # Action verbs check
        action_count = sum(1 for v in self.ACTION_VERBS if f" {v} " in f" {resume.lower()} ")
        score += min(action_count * 2, 20)

        # Section headers present
        sections = ["experience", "education", "skills", "projects", "summary"]
        found = sum(1 for s in sections if s in resume.lower())
        score += found * 2

        return max(0.0, min(100.0, score))
