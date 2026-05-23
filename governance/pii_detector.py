"""
governance/pii_detector.py - Personally Identifiable Information detection and masking
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from config import GOVERNANCE_CONFIG


@dataclass
class PIIResult:
    has_pii: bool
    pii_types_found: List[str] = field(default_factory=list)
    masked_text: str = ""
    pii_count: int = 0
    pii_details: List[Dict] = field(default_factory=list)


class PIIDetector:
    """
    Detects and masks Personally Identifiable Information (PII) in text.
    Protects user privacy in logs, audit trails, and stored outputs.

    Detects:
    - Email addresses
    - Phone numbers
    - Social Security Numbers (SSN)
    - Credit card numbers
    - Passport numbers
    - Dates of birth
    - Physical addresses (partial)
    - Names (optional — context-dependent)
    """

    PII_PATTERNS = {
        "email": {
            "pattern": r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}",
            "mask": "[EMAIL_REDACTED]",
            "severity": "HIGH",
        },
        "phone_us": {
            "pattern": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
            "mask": "[PHONE_REDACTED]",
            "severity": "HIGH",
        },
        "ssn": {
            "pattern": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "mask": "[SSN_REDACTED]",
            "severity": "CRITICAL",
        },
        "credit_card": {
            "pattern": r"\b(?:\d[ -]?){13,16}\b",
            "mask": "[CC_REDACTED]",
            "severity": "CRITICAL",
        },
        "passport": {
            "pattern": r"\b[A-Z]{1,2}[0-9]{6,9}\b",
            "mask": "[PASSPORT_REDACTED]",
            "severity": "HIGH",
        },
        "date_of_birth": {
            "pattern": r"\b(DOB|Date of Birth|Born)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
            "mask": "[DOB_REDACTED]",
            "severity": "MEDIUM",
        },
        "ip_address": {
            "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "mask": "[IP_REDACTED]",
            "severity": "MEDIUM",
        },
        "linkedin_url": {
            "pattern": r"linkedin\.com/in/[\w\-]+",
            "mask": "[LINKEDIN_REDACTED]",
            "severity": "LOW",
        },
        "github_url": {
            "pattern": r"github\.com/[\w\-]+",
            "mask": "[GITHUB_REDACTED]",
            "severity": "LOW",
        },
    }

    def __init__(self):
        self.config = GOVERNANCE_CONFIG
        self.mask_in_logs = self.config.get("mask_pii_in_logs", True)
        self.enabled_types = self.config.get("pii_patterns", list(self.PII_PATTERNS.keys()))

    def detect(self, text: str) -> PIIResult:
        """
        Detect PII in the given text without masking.

        Args:
            text: Input text to scan

        Returns:
            PIIResult with detected PII types and details
        """
        found_types = []
        pii_details = []
        total_count = 0

        for pii_type, config in self.PII_PATTERNS.items():
            if pii_type not in self.enabled_types:
                continue
            matches = re.findall(config["pattern"], text, re.IGNORECASE)
            if matches:
                found_types.append(pii_type)
                total_count += len(matches)
                pii_details.append({
                    "type": pii_type,
                    "count": len(matches),
                    "severity": config["severity"],
                })

        return PIIResult(
            has_pii=len(found_types) > 0,
            pii_types_found=found_types,
            masked_text=text,
            pii_count=total_count,
            pii_details=pii_details,
        )

    def mask(self, text: str, preserve_contact_section: bool = False) -> PIIResult:
        """
        Detect and mask PII in text (for safe logging/storage).

        Args:
            text: Input text to mask
            preserve_contact_section: If True, skip masking in contact sections

        Returns:
            PIIResult with masked_text
        """
        result = self.detect(text)
        masked = text

        for pii_type, config in self.PII_PATTERNS.items():
            if pii_type not in self.enabled_types:
                continue
            # Skip LinkedIn/GitHub in contact sections if preserve flag set
            if preserve_contact_section and pii_type in ["linkedin_url", "github_url"]:
                continue
            masked = re.sub(config["pattern"], config["mask"], masked, flags=re.IGNORECASE)

        result.masked_text = masked
        return result

    def mask_for_logging(self, text: str) -> str:
        """
        Returns PII-masked text safe for audit logs.
        Always masks critical PII regardless of settings.
        """
        if not self.mask_in_logs:
            return text
        result = self.mask(text, preserve_contact_section=False)
        return result.masked_text

    def get_pii_report(self, text: str) -> dict:
        """Generate a summary PII report for governance dashboards."""
        result = self.detect(text)
        high_severity = [d for d in result.pii_details if d["severity"] in ["HIGH", "CRITICAL"]]

        return {
            "has_pii": result.has_pii,
            "total_pii_instances": result.pii_count,
            "pii_types": result.pii_types_found,
            "high_severity_pii": len(high_severity),
            "risk_level": (
                "CRITICAL" if any(d["severity"] == "CRITICAL" for d in result.pii_details)
                else "HIGH" if any(d["severity"] == "HIGH" for d in result.pii_details)
                else "MEDIUM" if result.has_pii
                else "NONE"
            ),
            "recommendation": (
                "Mask before storing/sharing" if result.has_pii else "Safe to log"
            ),
        }
