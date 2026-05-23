"""
evaluation/cover_letter_evaluator.py - Evaluates cover letter quality
"""

import re
from typing import List
from config import EVALUATION_CONFIG
from .metrics import EvaluationMetrics, EvaluationReport, ScoreDimension


class CoverLetterEvaluator:
    """
    Evaluates cover letter quality across 4 dimensions:
    1. Relevance to JD     (35%)
    2. Tone & Voice        (25%)
    3. Structure           (20%)
    4. Personalization     (20%)
    """

    # Generic phrases that weaken cover letters
    GENERIC_PHRASES = [
        "i am writing to express my interest",
        "i believe i am the perfect candidate",
        "i am a hardworking individual",
        "please find my resume attached",
        "i look forward to hearing from you",
        "to whom it may concern",
        "i have always been passionate",
        "team player",
        "detail-oriented",
        "fast learner",
    ]

    # Strong personalization signals
    PERSONALIZATION_SIGNALS = [
        "your team", "your company", "your product", "your mission",
        "i noticed", "i admire", "i read about", "your recent",
        "your approach to", "your work on", "impressed by",
    ]

    def __init__(self):
        self.config = EVALUATION_CONFIG["cover_letter"]
        self.metrics = EvaluationMetrics()

    def evaluate(self, cover_letter: str, job_description: str, company_name: str) -> EvaluationReport:
        """
        Evaluate the quality of a cover letter.

        Args:
            cover_letter: Generated cover letter text
            job_description: Target job description
            company_name: Target company name

        Returns:
            EvaluationReport with detailed scoring
        """
        dimensions = []
        strengths = []
        improvements = []
        recommendations = []

        cl_lower = cover_letter.lower()
        word_count = self.metrics.count_words(cover_letter)

        # ── Dimension 1: Relevance (35%) ──────────────────────────
        jd_keywords = self.metrics.extract_keywords(job_description)[:30]
        relevance_score = self.metrics.keyword_overlap_score(cover_letter, jd_keywords)

        relevance_dim = ScoreDimension(
            name="Relevance to Job",
            score=relevance_score,
            weight=self.config["relevance_weight"],
            details=f"{int(relevance_score * len(jd_keywords) / 100)}/{len(jd_keywords)} JD keywords referenced",
            passed=relevance_score >= 50,
        )
        dimensions.append(relevance_dim)

        if relevance_score >= 70:
            strengths.append("Cover letter closely mirrors the job description language")
        elif relevance_score < 40:
            improvements.append("Cover letter doesn't reference key JD requirements — add specific role requirements")

        # ── Dimension 2: Tone & Voice (25%) ───────────────────────
        tone_score = self._score_tone(cover_letter)
        tone_dim = ScoreDimension(
            name="Tone & Voice",
            score=tone_score,
            weight=self.config["tone_weight"],
            details="Professional, confident, and engaging tone",
            passed=tone_score >= 60,
        )
        dimensions.append(tone_dim)

        generic_count = sum(1 for p in self.GENERIC_PHRASES if p in cl_lower)
        if generic_count == 0:
            strengths.append("Avoids generic, overused phrases")
        elif generic_count >= 3:
            improvements.append(f"Remove generic phrases ({generic_count} found) — they weaken your letter")
            recommendations.append('Replace "I am a hardworking team player" with specific achievements')

        # ── Dimension 3: Structure (20%) ──────────────────────────
        structure_score = self._score_structure(cover_letter)
        structure_dim = ScoreDimension(
            name="Structure & Format",
            score=structure_score,
            weight=self.config["structure_weight"],
            details=f"{word_count} words — ideal is 200-350 words",
            passed=structure_score >= 60,
        )
        dimensions.append(structure_dim)

        if 200 <= word_count <= 350:
            strengths.append(f"Ideal length ({word_count} words)")
        elif word_count < 150:
            improvements.append(f"Too short ({word_count} words). Expand with specific examples.")
        elif word_count > 450:
            improvements.append(f"Too long ({word_count} words). Keep it under 350 words.")

        # ── Dimension 4: Personalization (20%) ────────────────────
        personalization_score = self._score_personalization(cover_letter, company_name)
        personalization_dim = ScoreDimension(
            name="Personalization",
            score=personalization_score,
            weight=self.config["personalization_weight"],
            details=f"Company-specific content and unique value proposition",
            passed=personalization_score >= 50,
        )
        dimensions.append(personalization_dim)

        company_mentions = cl_lower.count(company_name.lower())
        if company_mentions >= 2:
            strengths.append(f"Company name referenced naturally ({company_mentions} times)")
        elif company_mentions == 0:
            improvements.append(f"Never mentions '{company_name}' — personalize for this company")

        personalization_signals_found = [s for s in self.PERSONALIZATION_SIGNALS if s in cl_lower]
        if len(personalization_signals_found) >= 2:
            strengths.append("Shows genuine interest in specific company aspects")
        elif not personalization_signals_found:
            improvements.append("Add company-specific details: mission, product, recent news")
            recommendations.append("Research the company and reference something specific to them")

        # ── Final Score ────────────────────────────────────────────
        overall = self.metrics.calculate_weighted_score(dimensions)
        grade = EvaluationMetrics.score_to_grade(overall)
        passed = overall >= self.config["pass_threshold"]

        if overall >= 80:
            recommendations.insert(0, "Strong cover letter! Review once and submit.")
        elif overall >= 65:
            recommendations.insert(0, "Good foundation. Apply the improvements above before submitting.")
        else:
            recommendations.insert(0, "Needs significant revision. Focus on relevance and personalization first.")

        return EvaluationReport(
            artifact_type="cover_letter",
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
                "generic_phrase_count": generic_count,
                "company_mentions": company_mentions,
                "personalization_signals": len(personalization_signals_found),
            },
        )

    def _score_tone(self, text: str) -> float:
        """Score tone quality of the cover letter."""
        score = 60.0

        # Penalize generic phrases
        generic_count = sum(1 for p in self.GENERIC_PHRASES if p in text.lower())
        score -= generic_count * 8

        # Reward confidence signals
        confidence_words = ["achieved", "delivered", "built", "led", "created", "designed", "drove"]
        confidence_count = sum(1 for w in confidence_words if w in text.lower())
        score += min(confidence_count * 5, 25)

        # Check for first-person overuse (I, I, I...)
        i_count = len(re.findall(r'\bI\b', text))
        word_count = len(text.split())
        if word_count > 0:
            i_ratio = i_count / word_count
            if i_ratio > 0.15:
                score -= 10  # Too I-heavy

        # Check for passive voice
        passive_count = len(re.findall(r'\b(was|were|been|being)\s+\w+ed\b', text, re.IGNORECASE))
        score -= passive_count * 3

        return max(20.0, min(100.0, score))

    def _score_structure(self, text: str) -> float:
        """Score structural quality of the cover letter."""
        score = 40.0
        word_count = self.metrics.count_words(text)
        sentence_count = self.metrics.count_sentences(text)

        # Ideal word count
        if 200 <= word_count <= 350:
            score += 30
        elif 150 <= word_count < 200 or 350 < word_count <= 450:
            score += 15

        # Has multiple paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            score += 20
        elif len(paragraphs) >= 2:
            score += 10

        # Has opening and closing
        has_opening = any(w in text[:200].lower() for w in ["dear", "hello", "to the"])
        has_closing = any(w in text[-200:].lower() for w in ["sincerely", "regards", "thank you"])
        if has_opening:
            score += 5
        if has_closing:
            score += 5

        return max(0.0, min(100.0, score))

    def _score_personalization(self, text: str, company_name: str) -> float:
        """Score personalization to the specific company."""
        score = 30.0

        # Company name mentioned
        mentions = text.lower().count(company_name.lower())
        score += min(mentions * 15, 30)

        # Personalization signals
        signals_found = sum(1 for s in self.PERSONALIZATION_SIGNALS if s in text.lower())
        score += min(signals_found * 10, 30)

        # Points for mentioning company values/products
        value_words = ["mission", "vision", "product", "platform", "culture", "values"]
        values_mentioned = sum(1 for v in value_words if v in text.lower())
        score += min(values_mentioned * 3, 10)

        return max(0.0, min(100.0, score))
