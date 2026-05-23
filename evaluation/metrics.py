"""
evaluation/metrics.py - Core scoring metrics and data structures
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ScoreDimension:
    name: str
    score: float          # 0-100
    weight: float         # 0-1, sum = 1.0
    weighted_score: float = 0.0
    details: str = ""
    passed: bool = True


@dataclass
class EvaluationReport:
    """
    Structured evaluation report returned by every evaluator.
    """
    artifact_type: str        # 'resume', 'cover_letter', 'interview_prep'
    overall_score: float      # 0-100
    grade: str               # A, B, C, D, F
    passed: bool
    threshold: float
    dimensions: List[ScoreDimension] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "artifact_type": self.artifact_type,
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "passed": self.passed,
            "threshold": self.threshold,
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 1),
                    "weight": d.weight,
                    "weighted_score": round(d.weighted_score, 1),
                    "details": d.details,
                    "passed": d.passed,
                }
                for d in self.dimensions
            ],
            "strengths": self.strengths,
            "improvements": self.improvements,
            "recommendations": self.recommendations,
            "evaluated_at": self.evaluated_at,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Format as human-readable text report."""
        lines = [
            f"{'='*60}",
            f"EVALUATION REPORT — {self.artifact_type.upper().replace('_', ' ')}",
            f"{'='*60}",
            f"Overall Score : {self.overall_score:.1f}/100  [{self.grade}]",
            f"Status        : {'✓ PASSED' if self.passed else '✗ NEEDS IMPROVEMENT'}",
            f"Threshold     : {self.threshold}/100",
            f"Evaluated At  : {self.evaluated_at}",
            "",
            "DIMENSION SCORES:",
            "-" * 40,
        ]
        for d in self.dimensions:
            status = "✓" if d.passed else "✗"
            lines.append(f"  {status} {d.name:<30} {d.score:.1f}/100  (weight: {d.weight:.0%})")
            if d.details:
                lines.append(f"    → {d.details}")

        if self.strengths:
            lines += ["", "STRENGTHS:", "-" * 40]
            lines += [f"  + {s}" for s in self.strengths]

        if self.improvements:
            lines += ["", "AREAS FOR IMPROVEMENT:", "-" * 40]
            lines += [f"  ! {i}" for i in self.improvements]

        if self.recommendations:
            lines += ["", "RECOMMENDATIONS:", "-" * 40]
            lines += [f"  → {r}" for r in self.recommendations]

        lines.append("=" * 60)
        return "\n".join(lines)


class EvaluationMetrics:
    """Utility functions for common scoring operations."""

    @staticmethod
    def score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def keyword_overlap_score(text: str, keywords: List[str]) -> float:
        """
        Calculate what percentage of keywords appear in text.
        Returns 0-100.
        """
        if not keywords:
            return 0.0
        text_lower = text.lower()
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        return (found / len(keywords)) * 100

    @staticmethod
    def calculate_weighted_score(dimensions: List[ScoreDimension]) -> float:
        """Calculate weighted total score from dimension list."""
        total = 0.0
        for d in dimensions:
            d.weighted_score = d.score * d.weight
            total += d.weighted_score
        return round(total, 2)

    @staticmethod
    def extract_keywords(text: str, min_length: int = 4) -> List[str]:
        """Extract meaningful keywords from text."""
        import re
        # Remove common stop words
        stop_words = {
            "with", "have", "will", "from", "this", "that", "they",
            "your", "their", "which", "would", "should", "could",
            "also", "been", "were", "when", "what", "about", "into",
            "than", "then", "them", "these", "those", "such", "most"
        }
        words = re.findall(r'\b[a-z]\w+\b', text.lower())
        return [w for w in words if len(w) >= min_length and w not in stop_words]

    @staticmethod
    def count_sentences(text: str) -> int:
        """Count approximate number of sentences."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
