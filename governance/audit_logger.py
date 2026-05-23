"""
governance/audit_logger.py - Full audit trail for all agent actions and decisions
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from config import GOVERNANCE_CONFIG


@dataclass
class AuditEvent:
    event_id: str
    timestamp: str
    event_type: str          # REQUEST, AGENT_CALL, TOOL_CALL, GOVERNANCE_CHECK, OUTPUT, ERROR
    agent_name: str
    action: str
    input_summary: str       # PII-masked summary
    output_summary: str      # PII-masked summary
    status: str              # SUCCESS, BLOCKED, FAILED, WARNING
    duration_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)
    governance_flags: List[str] = field(default_factory=list)


class AuditLogger:
    """
    Immutable audit trail for all pipeline operations.
    Records every agent call, tool use, governance decision, and output.
    Critical for compliance, debugging, and accountability.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.config = GOVERNANCE_CONFIG
        self.enabled = self.config.get("enable_audit_logging", True)
        self.log_path = Path(self.config.get("audit_log_path", "logs/audit.log"))
        self.events: List[AuditEvent] = []
        self._event_counter = 0
        self._setup_logger()

    def _setup_logger(self):
        """Set up file and console loggers."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"audit.{self.session_id}")
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # File handler
            fh = logging.FileHandler(self.log_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(fh)

    def _generate_event_id(self) -> str:
        self._event_counter += 1
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{self.session_id}_{ts}_{self._event_counter:04d}"

    def _truncate(self, text: str, max_len: int = 200) -> str:
        """Truncate long text for log summaries."""
        if not text:
            return ""
        text = str(text)
        return text[:max_len] + "..." if len(text) > max_len else text

    def log_event(
        self,
        event_type: str,
        agent_name: str,
        action: str,
        input_summary: str = "",
        output_summary: str = "",
        status: str = "SUCCESS",
        duration_ms: float = 0.0,
        metadata: Optional[Dict] = None,
        governance_flags: Optional[List[str]] = None,
    ) -> str:
        """
        Log a single audit event.

        Returns:
            event_id for reference
        """
        if not self.enabled:
            return ""

        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            agent_name=agent_name,
            action=action,
            input_summary=self._truncate(input_summary),
            output_summary=self._truncate(output_summary),
            status=status,
            duration_ms=round(duration_ms, 2),
            metadata=metadata or {},
            governance_flags=governance_flags or [],
        )

        self.events.append(event)
        self._write_event(event)
        return event.event_id

    def _write_event(self, event: AuditEvent):
        """Write event to log file as JSON line."""
        try:
            log_entry = json.dumps(asdict(event), ensure_ascii=False)
            self.logger.info(log_entry)
        except Exception as e:
            # Never crash the pipeline because of logging
            pass

    def log_request(self, action: str, input_summary: str, metadata: dict = None) -> str:
        return self.log_event("REQUEST", "system", action, input_summary=input_summary, metadata=metadata)

    def log_agent_call(self, agent_name: str, action: str, input_summary: str,
                       output_summary: str, duration_ms: float = 0.0, status: str = "SUCCESS") -> str:
        return self.log_event(
            "AGENT_CALL", agent_name, action,
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=duration_ms,
            status=status,
        )

    def log_tool_call(self, tool_name: str, args_summary: str,
                      result_summary: str, duration_ms: float = 0.0) -> str:
        return self.log_event(
            "TOOL_CALL", "tools", tool_name,
            input_summary=args_summary,
            output_summary=result_summary,
            duration_ms=duration_ms,
        )

    def log_governance(self, check_name: str, result: str,
                       flags: List[str] = None, status: str = "SUCCESS") -> str:
        return self.log_event(
            "GOVERNANCE_CHECK", "governance", check_name,
            output_summary=result,
            status=status,
            governance_flags=flags or [],
        )

    def log_output(self, output_type: str, summary: str, file_path: str = "") -> str:
        return self.log_event(
            "OUTPUT", "system", output_type,
            output_summary=summary,
            metadata={"file_path": file_path} if file_path else {},
        )

    def log_error(self, agent_name: str, action: str, error: str) -> str:
        return self.log_event(
            "ERROR", agent_name, action,
            output_summary=error,
            status="FAILED",
        )

    def get_session_summary(self) -> dict:
        """Generate a complete session audit summary."""
        total = len(self.events)
        by_type = {}
        by_status = {}

        for e in self.events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
            by_status[e.status] = by_status.get(e.status, 0) + 1

        all_flags = [flag for e in self.events for flag in e.governance_flags]
        errors = [e for e in self.events if e.status == "FAILED"]
        blocked = [e for e in self.events if e.status == "BLOCKED"]

        return {
            "session_id": self.session_id,
            "total_events": total,
            "events_by_type": by_type,
            "events_by_status": by_status,
            "governance_flags": list(set(all_flags)),
            "error_count": len(errors),
            "blocked_count": len(blocked),
            "log_file": str(self.log_path),
            "pipeline_health": "HEALTHY" if not errors and not blocked else "ISSUES_DETECTED",
        }

    def export_session_log(self) -> str:
        """Export full session log as JSON string."""
        return json.dumps(
            {
                "session_id": self.session_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "events": [asdict(e) for e in self.events],
            },
            indent=2,
        )
