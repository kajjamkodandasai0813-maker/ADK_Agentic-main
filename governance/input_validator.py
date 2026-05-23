"""
governance/input_validator.py - Validates all inputs before processing
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from config import GOVERNANCE_CONFIG


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_input: Optional[str] = None


class InputValidator:
    """
    Validates and sanitizes all inputs entering the pipeline.
    Acts as the first gate in the governance layer.
    """

    def __init__(self):
        self.config = GOVERNANCE_CONFIG
        self.max_resume_len = self.config["max_resume_length"]
        self.min_resume_len = self.config["min_resume_length"]
        self.max_jd_len = self.config["max_job_description_length"]
        self.min_jd_len = self.config["min_job_description_length"]
        self.allowed_extensions = self.config["allowed_file_types"]

    def validate_resume_text(self, resume_text: str) -> ValidationResult:
        """Validate resume text input."""
        errors = []
        warnings = []

        if not resume_text or not resume_text.strip():
            errors.append("Resume text cannot be empty.")
            return ValidationResult(is_valid=False, errors=errors)

        text = resume_text.strip()

        if len(text) < self.min_resume_len:
            errors.append(
                f"Resume too short ({len(text)} chars). Minimum is {self.min_resume_len} chars."
            )

        if len(text) > self.max_resume_len:
            warnings.append(
                f"Resume is very long ({len(text)} chars). Truncating to {self.max_resume_len} chars."
            )
            text = text[: self.max_resume_len]

        # Check for basic resume structure markers
        resume_markers = ["experience", "education", "skill", "work", "project", "summary"]
        found_markers = [m for m in resume_markers if m in text.lower()]
        if len(found_markers) < 2:
            warnings.append(
                "Resume may lack key sections (experience, education, skills). "
                "Results may be less accurate."
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=text,
        )

    def validate_job_description(self, jd_text: str) -> ValidationResult:
        """Validate job description text input."""
        errors = []
        warnings = []

        if not jd_text or not jd_text.strip():
            errors.append("Job description cannot be empty.")
            return ValidationResult(is_valid=False, errors=errors)

        text = jd_text.strip()

        if len(text) < self.min_jd_len:
            errors.append(
                f"Job description too short ({len(text)} chars). Minimum is {self.min_jd_len} chars."
            )

        if len(text) > self.max_jd_len:
            warnings.append(
                f"Job description truncated to {self.max_jd_len} chars."
            )
            text = text[: self.max_jd_len]

        # Check basic JD markers
        jd_markers = ["require", "responsibilit", "qualif", "experience", "skill", "role", "position"]
        found = [m for m in jd_markers if m in text.lower()]
        if len(found) < 2:
            warnings.append(
                "Job description may be incomplete. Ensure it includes responsibilities and requirements."
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=text,
        )

    def validate_company_name(self, company_name: str) -> ValidationResult:
        """Validate company name input."""
        errors = []
        warnings = []

        if not company_name or not company_name.strip():
            errors.append("Company name cannot be empty.")
            return ValidationResult(is_valid=False, errors=errors)

        name = company_name.strip()

        if len(name) < 2:
            errors.append("Company name too short.")
        if len(name) > 200:
            errors.append("Company name too long (max 200 chars).")

        # Check for suspicious patterns
        if any(char in name for char in ["<", ">", "{", "}", ";"]):
            errors.append("Company name contains invalid characters.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=name.strip(),
        )

    def validate_file_path(self, file_path: str) -> ValidationResult:
        """Validate that a file path is safe and supported."""
        errors = []
        warnings = []

        if not file_path:
            errors.append("File path cannot be empty.")
            return ValidationResult(is_valid=False, errors=errors)

        path = Path(file_path)

        if not path.exists():
            errors.append(f"File does not exist: {file_path}")
            return ValidationResult(is_valid=False, errors=errors)

        if path.suffix.lower() not in self.allowed_extensions:
            errors.append(
                f"Unsupported file type: '{path.suffix}'. "
                f"Allowed: {', '.join(self.allowed_extensions)}"
            )

        # Check file size (max 10MB)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            errors.append(f"File too large: {size_mb:.1f}MB. Maximum is 10MB.")
        elif size_mb > 5:
            warnings.append(f"Large file ({size_mb:.1f}MB) may slow processing.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=str(path.resolve()),
        )

    def validate_pipeline_inputs(
        self, resume_text: str, job_description: str, company_name: str
    ) -> ValidationResult:
        """
        Validate all inputs together for the full pipeline.
        Returns combined validation result.
        """
        all_errors = []
        all_warnings = []

        r = self.validate_resume_text(resume_text)
        jd = self.validate_job_description(job_description)
        cn = self.validate_company_name(company_name)

        all_errors.extend(r.errors + jd.errors + cn.errors)
        all_warnings.extend(r.warnings + jd.warnings + cn.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            sanitized_input="all_valid",
        )
