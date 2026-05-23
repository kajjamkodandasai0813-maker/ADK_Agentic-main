"""
governance/content_filter.py - Detects and blocks harmful, unethical, or inappropriate content
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple
from config import GOVERNANCE_CONFIG


@dataclass
class FilterResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    filtered_content: str = ""
    risk_score: float = 0.0  # 0.0 (safe) to 1.0 (dangerous)


class ContentFilter:
    """
    Multi-layer content filter that screens inputs and outputs for:
    - Harmful/unethical content
    - Discrimination or bias indicators
    - Fraudulent intent
    - Inappropriate material
    """

    # Hard-blocked patterns (always rejected)
    HARD_BLOCK_PATTERNS = [
        (r"fake\s+(?:\w+\s+)?(degree|certificate|diploma|credential)", "Requesting fake credentials"),
        (r"forged?\s+(?:\w+\s+)?(document|signature|reference)", "Requesting document forgery"),
        (r"fabricat\w+\s+(?:\w+\s+)?(experience|work|employment)", "Requesting fabricated work history"),
        (r"lie\s+(about|on)\s+(resume|application|experience)", "Requesting dishonest content"),
        (r"plagiari[sz]", "Plagiarism detected"),
        (r"hack\s+(into|the)\s+\w+\s+(system|database|account)", "Malicious hacking intent"),
        (r"discriminat\w+\s+(against|based on)\s+(race|gender|age|religion|disability)", "Discriminatory content"),
        (r"illegal\s+(immigration|work\s+authorization|visa\s+fraud)", "Illegal activity"),
    ]

    # Soft warnings (flag but allow with warning)
    SOFT_WARNING_PATTERNS = [
        (r"embellish\w*|stretch\s+the\s+truth|exaggerat\w+", "May encourage resume embellishment"),
        (r"hide\s+(gap|employment\s+gap|career\s+gap)", "Hiding employment gaps — advise honest framing instead"),
        (r"years?\s+of\s+experience.{0,20}(more than|over|at least).{0,10}\d+", "Check experience claims match reality"),
    ]

    # Bias indicators in job descriptions (for awareness)
    BIAS_PATTERNS = [
        (r"\b(he|she)\s+(should|must|will)\b", "Gender-biased language in JD"),
        (r"young\s+(professional|candidate|graduate)", "Age-biased language in JD"),
        (r"native\s+speaker\s+only", "Potentially discriminatory language requirement"),
        (r"recent\s+graduate\s+only", "May exclude experienced candidates illegally"),
    ]

    def __init__(self):
        self.config = GOVERNANCE_CONFIG
        self.blocked_keywords = [kw.lower() for kw in self.config.get("blocked_keywords", [])]

    def filter_content(self, content: str, content_type: str = "general") -> FilterResult:
        """
        Filter content for safety violations.

        Args:
            content: Text to filter
            content_type: 'resume', 'job_description', 'output', or 'general'

        Returns:
            FilterResult with is_safe flag and details
        """
        violations = []
        warnings = []
        risk_score = 0.0

        content_lower = content.lower()

        # Check hard block patterns
        for pattern, description in self.HARD_BLOCK_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                violations.append(f"BLOCKED: {description}")
                risk_score = min(risk_score + 0.4, 1.0)

        # Check config-level blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in content_lower:
                violations.append(f"BLOCKED: Prohibited keyword detected — '{keyword}'")
                risk_score = min(risk_score + 0.3, 1.0)

        # Check soft warnings
        for pattern, description in self.SOFT_WARNING_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                warnings.append(f"WARNING: {description}")
                risk_score = min(risk_score + 0.1, 1.0)

        # Check bias patterns for JD content
        if content_type == "job_description":
            for pattern, description in self.BIAS_PATTERNS:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    warnings.append(f"BIAS ALERT: {description}")
                    risk_score = min(risk_score + 0.05, 1.0)

        is_safe = len(violations) == 0

        # If safe, clean the content lightly
        filtered_content = content if is_safe else ""

        return FilterResult(
            is_safe=is_safe,
            violations=violations,
            warnings=warnings,
            filtered_content=filtered_content,
            risk_score=round(risk_score, 2),
        )

    def filter_output(self, output: str) -> FilterResult:
        """
        Filter generated output before returning to user.
        Ensures LLM output doesn't contain harmful advice.
        """
        return self.filter_content(output, content_type="output")

    def filter_job_description(self, jd: str) -> FilterResult:
        """
        Filter job description specifically — checks for discriminatory language.
        """
        result = self.filter_content(jd, content_type="job_description")

        # Additional JD-specific check: unrealistic requirements
        if "10+ years" in jd and "entry level" in jd.lower():
            result.warnings.append(
                "WARNING: JD lists '10+ years experience' for an 'entry level' role — possibly unrealistic."
            )

        return result

    def get_safety_report(self, results: List[FilterResult]) -> dict:
        """Generate a consolidated safety report from multiple filter results."""
        total_violations = sum(len(r.violations) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        avg_risk = sum(r.risk_score for r in results) / len(results) if results else 0.0

        return {
            "overall_safe": all(r.is_safe for r in results),
            "total_violations": total_violations,
            "total_warnings": total_warnings,
            "average_risk_score": round(avg_risk, 2),
            "risk_level": (
                "HIGH" if avg_risk > 0.5
                else "MEDIUM" if avg_risk > 0.2
                else "LOW"
            ),
            "all_violations": [v for r in results for v in r.violations],
            "all_warnings": [w for r in results for w in r.warnings],
        }
