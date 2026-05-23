"""
memory/session_manager.py - Session state management across the pipeline
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from config import SESSION_CONFIG


@dataclass
class ApplicationSession:
    """
    Represents a single job application session.
    Stores all context needed for the pipeline to run.
    """
    session_id: str
    created_at: str
    last_updated: str

    # Input data
    raw_resume: str = ""
    job_description: str = ""
    company_name: str = ""
    target_role: str = ""
    applicant_name: str = ""

    # Parsed/structured data
    parsed_resume: Dict = field(default_factory=dict)
    company_research: Dict = field(default_factory=dict)
    salary_data: Dict = field(default_factory=dict)
    job_market_data: Dict = field(default_factory=dict)

    # Agent outputs
    tailored_resume: str = ""
    cover_letter: str = ""
    interview_prep: str = ""

    # Evaluation results
    resume_evaluation: Dict = field(default_factory=dict)
    cover_letter_evaluation: Dict = field(default_factory=dict)
    interview_evaluation: Dict = field(default_factory=dict)
    master_report: str = ""

    # Governance records
    governance_flags: List[str] = field(default_factory=list)
    audit_events: List[str] = field(default_factory=list)

    # Output file paths
    output_files: Dict[str, str] = field(default_factory=dict)

    # Pipeline state
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    status: str = "initialized"  # initialized, running, completed, failed

    def mark_step_complete(self, step: str):
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def mark_step_failed(self, step: str, error: str = ""):
        if step not in self.failed_steps:
            self.failed_steps.append(step)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def is_step_done(self, step: str) -> bool:
        return step in self.completed_steps

    def to_dict(self) -> dict:
        return asdict(self)

    def get_progress(self) -> dict:
        pipeline_steps = [
            "input_validation", "content_filtering",
            "resume_parsing", "company_research", "salary_research",
            "resume_tailoring", "cover_letter_writing", "interview_prep",
            "resume_evaluation", "cover_letter_evaluation",
            "interview_evaluation", "master_report", "file_export",
        ]
        done = len(self.completed_steps)
        total = len(pipeline_steps)
        return {
            "completed": done,
            "total": total,
            "percentage": round((done / total) * 100, 1) if total > 0 else 0,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "status": self.status,
        }


class SessionManager:
    """
    Manages the lifecycle of application sessions.
    Supports in-memory and file-based storage.
    """

    def __init__(self):
        self.config = SESSION_CONFIG
        self.storage_type = self.config.get("session_storage", "memory")
        self.max_sessions = self.config.get("max_sessions", 100)
        self.ttl_hours = self.config.get("session_ttl_hours", 24)

        # In-memory store
        self._sessions: Dict[str, ApplicationSession] = {}

        # File store path
        self._file_path = Path(self.config.get("session_file_path", "sessions/sessions.json"))

        # Load from file if file-based
        if self.storage_type == "file":
            self._load_from_file()

    def create_session(
        self,
        resume_text: str = "",
        job_description: str = "",
        company_name: str = "",
        target_role: str = "",
        applicant_name: str = "",
    ) -> ApplicationSession:
        """
        Create a new application session.

        Returns:
            New ApplicationSession with unique session_id
        """
        # Enforce max sessions limit
        if len(self._sessions) >= self.max_sessions:
            self._evict_oldest_session()

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        session = ApplicationSession(
            session_id=session_id,
            created_at=now,
            last_updated=now,
            raw_resume=resume_text,
            job_description=job_description,
            company_name=company_name,
            target_role=target_role,
            applicant_name=applicant_name,
            status="initialized",
        )

        self._sessions[session_id] = session

        if self.storage_type == "file":
            self._save_to_file()

        return session

    def get_session(self, session_id: str) -> Optional[ApplicationSession]:
        """Retrieve a session by ID."""
        session = self._sessions.get(session_id)
        if session and self._is_expired(session):
            self.delete_session(session_id)
            return None
        return session

    def update_session(self, session: ApplicationSession) -> None:
        """Persist session updates."""
        session.last_updated = datetime.now(timezone.utc).isoformat()
        self._sessions[session.session_id] = session
        if self.storage_type == "file":
            self._save_to_file()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self.storage_type == "file":
                self._save_to_file()
            return True
        return False

    def list_sessions(self) -> List[dict]:
        """List all active sessions with basic info."""
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at,
                "status": s.status,
                "company": s.company_name,
                "role": s.target_role,
                "progress": s.get_progress(),
            }
            for s in self._sessions.values()
            if not self._is_expired(s)
        ]

    def _is_expired(self, session: ApplicationSession) -> bool:
        """Check if session has exceeded TTL."""
        try:
            created = datetime.fromisoformat(session.created_at)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - created
            return age > timedelta(hours=self.ttl_hours)
        except Exception:
            return False

    def _evict_oldest_session(self) -> None:
        """Remove the oldest session when at capacity."""
        if not self._sessions:
            return
        oldest_id = min(self._sessions.keys(), key=lambda k: self._sessions[k].created_at)
        self.delete_session(oldest_id)

    def _save_to_file(self) -> None:
        """Save all sessions to JSON file."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            data = {sid: s.to_dict() for sid, s in self._sessions.items()}
            self._file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_from_file(self) -> None:
        """Load sessions from JSON file."""
        try:
            if self._file_path.exists():
                data = json.loads(self._file_path.read_text(encoding="utf-8"))
                for sid, sdata in data.items():
                    session = ApplicationSession(**sdata)
                    if not self._is_expired(session):
                        self._sessions[sid] = session
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Return session manager statistics."""
        sessions = list(self._sessions.values())
        return {
            "total_sessions": len(sessions),
            "active_sessions": sum(1 for s in sessions if s.status == "running"),
            "completed_sessions": sum(1 for s in sessions if s.status == "completed"),
            "failed_sessions": sum(1 for s in sessions if s.status == "failed"),
            "max_capacity": self.max_sessions,
            "storage_type": self.storage_type,
        }
