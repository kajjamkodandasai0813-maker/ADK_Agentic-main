"""
config.py - Central configuration for Job Application Assistant
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# LLM Configuration
# ─────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))

# ─────────────────────────────────────────────
# Agent Configuration
# ─────────────────────────────────────────────
AGENT_CONFIG = {
    "orchestrator": {
        "name": "JobApplicationOrchestrator",
        "description": "Master orchestrator that coordinates all job application sub-agents",
        "max_iterations": 10,
    },
    "resume_parser": {
        "name": "ResumeParserAgent",
        "description": "Parses and extracts structured information from resumes",
        "max_iterations": 3,
    },
    "job_research": {
        "name": "JobResearchAgent",
        "description": "Researches companies, roles, and job market trends",
        "max_iterations": 5,
    },
    "resume_tailor": {
        "name": "ResumeTailorAgent",
        "description": "Tailors resume to match specific job descriptions",
        "max_iterations": 5,
    },
    "cover_letter": {
        "name": "CoverLetterAgent",
        "description": "Writes personalized, compelling cover letters",
        "max_iterations": 3,
    },
    "interview_prep": {
        "name": "InterviewPrepAgent",
        "description": "Generates interview questions, answers, and strategy",
        "max_iterations": 5,
    },
}

# ─────────────────────────────────────────────
# Governance Configuration
# ─────────────────────────────────────────────
GOVERNANCE_CONFIG = {
    # Input validation
    "max_resume_length": 50000,          # characters
    "max_job_description_length": 20000, # characters
    "min_resume_length": 100,
    "min_job_description_length": 50,
    "allowed_file_types": [".pdf", ".docx", ".txt"],

    # Rate limiting
    "rate_limit_requests_per_minute": 20,
    "rate_limit_tokens_per_minute": 100000,

    # Content filtering
    "blocked_keywords": [
        "hack", "exploit", "fraud", "fake degree",
        "forged", "plagiarize", "discriminate"
    ],

    # PII settings
    "mask_pii_in_logs": True,
    "pii_patterns": ["email", "phone", "ssn", "dob"],

    # Audit
    "audit_log_path": "logs/audit.log",
    "enable_audit_logging": True,
}

# ─────────────────────────────────────────────
# Evaluation Configuration
# ─────────────────────────────────────────────
EVALUATION_CONFIG = {
    "resume_match": {
        "keyword_weight": 0.40,
        "skills_weight": 0.30,
        "experience_weight": 0.20,
        "format_weight": 0.10,
        "pass_threshold": 60.0,
    },
    "cover_letter": {
        "relevance_weight": 0.35,
        "tone_weight": 0.25,
        "structure_weight": 0.20,
        "personalization_weight": 0.20,
        "pass_threshold": 65.0,
    },
    "interview_prep": {
        "question_relevance_weight": 0.40,
        "answer_quality_weight": 0.40,
        "coverage_weight": 0.20,
        "pass_threshold": 70.0,
    },
}

# ─────────────────────────────────────────────
# Output Configuration
# ─────────────────────────────────────────────
OUTPUT_CONFIG = {
    "output_dir": "outputs",
    "save_tailored_resume": True,
    "save_cover_letter": True,
    "save_interview_prep": True,
    "save_evaluation_report": True,
    "report_format": "txt",  # txt or pdf
}

# ─────────────────────────────────────────────
# Session Configuration
# ─────────────────────────────────────────────
SESSION_CONFIG = {
    "session_storage": "memory",  # memory or file
    "session_file_path": "sessions/sessions.json",
    "max_sessions": 100,
    "session_ttl_hours": 24,
}
