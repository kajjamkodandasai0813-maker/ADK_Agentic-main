"""
agents/orchestrator.py - Master orchestrator that coordinates all sub-agents
"""

import time
from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .resume_parser_agent import ResumeParserAgent
from .job_research_agent import JobResearchAgent
from .resume_tailor_agent import ResumeTailorAgent
from .cover_letter_agent import CoverLetterAgent
from .interview_prep_agent import InterviewPrepAgent

from governance.input_validator import InputValidator
from governance.content_filter import ContentFilter
from governance.pii_detector import PIIDetector
from governance.rate_limiter import RateLimiter
from governance.audit_logger import AuditLogger

from evaluation.evaluator import MasterEvaluator
from memory.session_manager import SessionManager, ApplicationSession
from tools.file_tools import write_text_file, write_json_file

console = Console()


class JobApplicationOrchestrator:
    """
    Master orchestrator that runs the complete job application pipeline:

    1. Governance Gate (input validation, content filtering, PII check)
    2. Resume Parsing Agent
    3. Job Research Agent (company + market + JD analysis)
    4. Resume Tailoring Agent
    5. Cover Letter Agent
    6. Interview Prep Agent
    7. Evaluation (resume + cover letter + interview)
    8. Master Report Generation
    9. File Export
    """

    PIPELINE_STEPS = [
        "input_validation",
        "content_filtering",
        "resume_parsing",
        "company_research",
        "resume_tailoring",
        "cover_letter_writing",
        "interview_prep",
        "resume_evaluation",
        "cover_letter_evaluation",
        "interview_evaluation",
        "master_report",
        "file_export",
    ]

    def __init__(self):
        # Governance layer
        self.validator = InputValidator()
        self.content_filter = ContentFilter()
        self.pii_detector = PIIDetector()
        self.rate_limiter = RateLimiter()

        # Agents
        self.resume_parser = ResumeParserAgent()
        self.job_researcher = JobResearchAgent()
        self.resume_tailor = ResumeTailorAgent()
        self.cover_letter_writer = CoverLetterAgent()
        self.interview_prepper = InterviewPrepAgent()

        # Evaluation
        self.evaluator = MasterEvaluator()

        # Memory
        self.session_manager = SessionManager()

    def run(
        self,
        resume_text: str,
        job_description: str,
        company_name: str,
        target_role: str = "",
        applicant_name: str = "Applicant",
    ) -> Dict[str, Any]:
        """
        Execute the complete job application pipeline.

        Args:
            resume_text: Raw resume text
            job_description: Target job description
            company_name: Name of target company
            target_role: Job title being applied for
            applicant_name: Candidate's name

        Returns:
            Complete pipeline results with all outputs and evaluations
        """
        # ── Create session ─────────────────────────────────────────
        session = self.session_manager.create_session(
            resume_text=resume_text,
            job_description=job_description,
            company_name=company_name,
            target_role=target_role,
            applicant_name=applicant_name,
        )
        session.status = "running"

        audit = AuditLogger(session_id=session.session_id)
        audit.log_request(
            action="pipeline_start",
            input_summary=f"Role: {target_role} | Company: {company_name} | Resume: {len(resume_text)} chars",
        )

        console.print(Panel(
            f"[bold cyan]Job Application Pipeline Starting[/bold cyan]\n"
            f"Session: [yellow]{session.session_id}[/yellow]\n"
            f"Role   : [green]{target_role}[/green] @ [green]{company_name}[/green]",
            title="🚀 Orchestrator"
        ))

        pipeline_data: Dict[str, Any] = {
            "session_id": session.session_id,
            "raw_resume": resume_text,
            "job_description": job_description,
            "company_name": company_name,
            "target_role": target_role,
            "applicant_name": applicant_name,
        }

        # ═══════════════════════════════════════════════════════════
        # STAGE 1: GOVERNANCE GATE
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 1: Governance Gate ━━[/bold yellow]")

        # Input Validation
        validation_result = self.validator.validate_pipeline_inputs(
            resume_text, job_description, company_name
        )
        if not validation_result.is_valid:
            audit.log_governance("input_validation", "FAILED", validation_result.errors, "BLOCKED")
            session.mark_step_failed("input_validation", str(validation_result.errors))
            session.status = "failed"
            self.session_manager.update_session(session)
            return self._pipeline_failed(
                "Input validation failed", validation_result.errors, session, audit
            )

        if validation_result.warnings:
            for w in validation_result.warnings:
                console.print(f"  [yellow]⚠ {w}[/yellow]")

        session.governance_flags.extend(validation_result.warnings)
        audit.log_governance("input_validation", "PASSED")
        session.mark_step_complete("input_validation")
        console.print("  [green]✓ Input validation passed[/green]")

        # Content Filtering
        resume_filter = self.content_filter.filter_content(resume_text, "resume")
        jd_filter = self.content_filter.filter_job_description(job_description)

        all_filter_results = [resume_filter, jd_filter]
        safety_report = self.content_filter.get_safety_report(all_filter_results)

        if not safety_report["overall_safe"]:
            audit.log_governance("content_filtering", "BLOCKED",
                                 safety_report["all_violations"], "BLOCKED")
            return self._pipeline_failed(
                "Content filtering blocked", safety_report["all_violations"], session, audit
            )

        if safety_report["all_warnings"]:
            for w in safety_report["all_warnings"]:
                console.print(f"  [yellow]⚠ {w}[/yellow]")

        session.governance_flags.extend(safety_report["all_warnings"])
        audit.log_governance("content_filtering", f"PASSED — Risk: {safety_report['risk_level']}")
        session.mark_step_complete("content_filtering")
        console.print(f"  [green]✓ Content filter passed (Risk: {safety_report['risk_level']})[/green]")

        # PII Detection
        pii_report = self.pii_detector.get_pii_report(resume_text)
        if pii_report["has_pii"]:
            console.print(f"  [cyan]ℹ PII detected ({pii_report['total_pii_instances']} instances) — masking for logs[/cyan]")
        audit.log_governance(
            "pii_detection",
            f"PII found: {pii_report['has_pii']} | Risk: {pii_report['risk_level']}"
        )

        # Rate Limiting
        rate_check = self.rate_limiter.check_request(estimated_tokens=20000)
        if not rate_check.allowed:
            return self._pipeline_failed(
                f"Rate limit: {rate_check.reason}", [], session, audit
            )
        self.rate_limiter.record_request(tokens_used=20000)

        # ═══════════════════════════════════════════════════════════
        # STAGE 2: RESUME PARSING
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 2: Resume Parsing ━━[/bold yellow]")
        t0 = time.time()

        parser_result = self.resume_parser.run(pipeline_data)
        duration = (time.time() - t0) * 1000

        if parser_result.get("success"):
            pipeline_data["parsed_resume"] = parser_result["parsed_resume"]
            session.parsed_resume = parser_result["parsed_resume"]
            session.mark_step_complete("resume_parsing")
            audit.log_agent_call("ResumeParserAgent", "parse_resume",
                                 "Resume text", "Structured resume data", duration)
            console.print(f"  [green]✓ Resume parsed successfully ({duration:.0f}ms)[/green]")
        else:
            console.print(f"  [yellow]⚠ Resume parsing had issues: {parser_result.get('error')}[/yellow]")
            pipeline_data["parsed_resume"] = ""
            session.mark_step_failed("resume_parsing")

        # ═══════════════════════════════════════════════════════════
        # STAGE 3: JOB RESEARCH
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 3: Job Research ━━[/bold yellow]")
        t0 = time.time()

        research_result = self.job_researcher.run(pipeline_data)
        duration = (time.time() - t0) * 1000

        if research_result.get("success"):
            pipeline_data["company_research"] = research_result["company_research"]
            pipeline_data["salary_data"] = research_result["salary_data"]
            pipeline_data["job_market_data"] = research_result["job_market_data"]
            pipeline_data["jd_analysis"] = research_result["jd_analysis"]

            session.company_research = research_result["company_research"]
            session.salary_data = research_result["salary_data"]
            session.job_market_data = research_result["job_market_data"]
            session.mark_step_complete("company_research")
            audit.log_agent_call("JobResearchAgent", "research_job",
                                 company_name, "Company + market + JD data", duration)
            console.print(f"  [green]✓ Research complete ({duration:.0f}ms)[/green]")
        else:
            console.print(f"  [yellow]⚠ Research incomplete: {research_result.get('error')}[/yellow]")
            session.mark_step_failed("company_research")

        # ═══════════════════════════════════════════════════════════
        # STAGE 4: RESUME TAILORING
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 4: Resume Tailoring ━━[/bold yellow]")
        t0 = time.time()

        tailor_result = self.resume_tailor.run(pipeline_data)
        duration = (time.time() - t0) * 1000

        if tailor_result.get("success"):
            pipeline_data["tailored_resume"] = tailor_result["tailored_resume"]
            session.tailored_resume = tailor_result["tailored_resume"]
            session.mark_step_complete("resume_tailoring")
            audit.log_agent_call("ResumeTailorAgent", "tailor_resume",
                                 "Original resume + JD", "Tailored resume", duration)
            console.print(f"  [green]✓ Resume tailored ({duration:.0f}ms)[/green]")
        else:
            console.print(f"  [red]✗ Resume tailoring failed: {tailor_result.get('error')}[/red]")
            pipeline_data["tailored_resume"] = resume_text
            session.mark_step_failed("resume_tailoring")

        # ═══════════════════════════════════════════════════════════
        # STAGE 5: COVER LETTER
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 5: Cover Letter Writing ━━[/bold yellow]")
        t0 = time.time()

        cl_result = self.cover_letter_writer.run(pipeline_data)
        duration = (time.time() - t0) * 1000

        if cl_result.get("success"):
            pipeline_data["cover_letter"] = cl_result["cover_letter"]
            session.cover_letter = cl_result["cover_letter"]
            session.mark_step_complete("cover_letter_writing")
            audit.log_agent_call("CoverLetterAgent", "write_cover_letter",
                                 "Resume + JD + company research", "Cover letter", duration)
            console.print(f"  [green]✓ Cover letter written ({duration:.0f}ms)[/green]")
        else:
            console.print(f"  [red]✗ Cover letter failed: {cl_result.get('error')}[/red]")
            pipeline_data["cover_letter"] = ""
            session.mark_step_failed("cover_letter_writing")

        # ═══════════════════════════════════════════════════════════
        # STAGE 6: INTERVIEW PREP
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 6: Interview Preparation ━━[/bold yellow]")
        t0 = time.time()

        interview_result = self.interview_prepper.run(pipeline_data)
        duration = (time.time() - t0) * 1000

        if interview_result.get("success"):
            pipeline_data["interview_prep"] = interview_result["interview_prep"]
            session.interview_prep = interview_result["interview_prep"]
            session.mark_step_complete("interview_prep")
            audit.log_agent_call("InterviewPrepAgent", "prepare_interview",
                                 "Resume + JD + company", "Interview prep guide", duration)
            console.print(f"  [green]✓ Interview prep generated ({duration:.0f}ms) — {interview_result.get('sections', 0)} sections[/green]")
        else:
            console.print(f"  [red]✗ Interview prep failed: {interview_result.get('error')}[/red]")
            pipeline_data["interview_prep"] = ""
            session.mark_step_failed("interview_prep")

        # ═══════════════════════════════════════════════════════════
        # STAGE 7: EVALUATION
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 7: Evaluation ━━[/bold yellow]")

        # Resume evaluation
        if pipeline_data.get("tailored_resume"):
            resume_eval = self.evaluator.evaluate_resume(
                pipeline_data["tailored_resume"], job_description
            )
            session.resume_evaluation = resume_eval.to_dict()
            session.mark_step_complete("resume_evaluation")
            console.print(f"  [green]✓ Resume: {resume_eval.overall_score:.1f}/100 [{resume_eval.grade}][/green]")
        else:
            resume_eval = None
            console.print("  [yellow]⚠ Resume evaluation skipped[/yellow]")

        # Cover letter evaluation
        if pipeline_data.get("cover_letter"):
            cl_eval = self.evaluator.evaluate_cover_letter(
                pipeline_data["cover_letter"], job_description, company_name
            )
            session.cover_letter_evaluation = cl_eval.to_dict()
            session.mark_step_complete("cover_letter_evaluation")
            console.print(f"  [green]✓ Cover Letter: {cl_eval.overall_score:.1f}/100 [{cl_eval.grade}][/green]")
        else:
            cl_eval = None
            console.print("  [yellow]⚠ Cover letter evaluation skipped[/yellow]")

        # Interview prep evaluation
        if pipeline_data.get("interview_prep"):
            interview_eval = self.evaluator.evaluate_interview_prep(
                pipeline_data["interview_prep"], job_description
            )
            session.interview_evaluation = interview_eval.to_dict()
            session.mark_step_complete("interview_evaluation")
            console.print(f"  [green]✓ Interview Prep: {interview_eval.overall_score:.1f}/100 [{interview_eval.grade}][/green]")
        else:
            interview_eval = None
            console.print("  [yellow]⚠ Interview eval skipped[/yellow]")

        # ═══════════════════════════════════════════════════════════
        # STAGE 8: MASTER REPORT
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 8: Master Report ━━[/bold yellow]")
        master_report = ""
        if resume_eval and cl_eval and interview_eval:
            master_report = self.evaluator.generate_master_report(
                resume_eval, cl_eval, interview_eval,
                user_info={
                    "name": applicant_name,
                    "role": target_role,
                    "company": company_name,
                }
            )
            session.master_report = master_report
            session.mark_step_complete("master_report")
            console.print("  [green]✓ Master evaluation report generated[/green]")

        # ═══════════════════════════════════════════════════════════
        # STAGE 9: FILE EXPORT
        # ═══════════════════════════════════════════════════════════
        console.print("\n[bold yellow]━━ Stage 9: File Export ━━[/bold yellow]")
        output_files = {}

        if session.tailored_resume:
            r = write_text_file("tailored_resume.txt", session.tailored_resume, sub_folder="resumes")
            if r["success"]:
                output_files["tailored_resume"] = r["file_path"]
                audit.log_output("tailored_resume", "Saved", r["file_path"])
                console.print(f"  [green]✓ Resume saved: {r['file_name']}[/green]")

        if session.cover_letter:
            r = write_text_file("cover_letter.txt", session.cover_letter, sub_folder="cover_letters")
            if r["success"]:
                output_files["cover_letter"] = r["file_path"]
                audit.log_output("cover_letter", "Saved", r["file_path"])
                console.print(f"  [green]✓ Cover letter saved: {r['file_name']}[/green]")

        if session.interview_prep:
            r = write_text_file("interview_prep.txt", session.interview_prep, sub_folder="interview_prep")
            if r["success"]:
                output_files["interview_prep"] = r["file_path"]
                audit.log_output("interview_prep", "Saved", r["file_path"])
                console.print(f"  [green]✓ Interview prep saved: {r['file_name']}[/green]")

        if master_report:
            r = write_text_file("evaluation_report.txt", master_report, sub_folder="reports")
            if r["success"]:
                output_files["evaluation_report"] = r["file_path"]
                audit.log_output("evaluation_report", "Saved", r["file_path"])
                console.print(f"  [green]✓ Evaluation report saved: {r['file_name']}[/green]")

        # Save session JSON
        session_data_export = write_json_file(
            f"session_{session.session_id}.json",
            session.to_dict(),
            sub_folder="sessions"
        )
        if session_data_export["success"]:
            output_files["session_data"] = session_data_export["file_path"]

        session.output_files = output_files
        session.mark_step_complete("file_export")
        session.status = "completed"
        self.session_manager.update_session(session)

        # Audit summary
        audit_summary = audit.get_session_summary()
        console.print("\n" + Panel(
            f"[bold green]Pipeline Complete![/bold green]\n\n"
            f"Session     : {session.session_id}\n"
            f"Progress    : {session.get_progress()['percentage']}%\n"
            f"Files saved : {len(output_files)}\n"
            f"Audit events: {audit_summary['total_events']}\n"
            f"Health      : {audit_summary['pipeline_health']}",
            title="✅ Done"
        ))

        return {
            "success": True,
            "session_id": session.session_id,
            "outputs": {
                "parsed_resume": pipeline_data.get("parsed_resume", ""),
                "jd_analysis": pipeline_data.get("jd_analysis", ""),
                "tailored_resume": pipeline_data.get("tailored_resume", ""),
                "cover_letter": pipeline_data.get("cover_letter", ""),
                "interview_prep": pipeline_data.get("interview_prep", ""),
                "master_report": master_report,
            },
            "evaluations": {
                "resume": resume_eval.to_dict() if resume_eval else {},
                "cover_letter": cl_eval.to_dict() if cl_eval else {},
                "interview_prep": interview_eval.to_dict() if interview_eval else {},
            },
            "output_files": output_files,
            "governance": {
                "flags": session.governance_flags,
                "audit_summary": audit_summary,
                "rate_limiter_stats": self.rate_limiter.get_stats(),
            },
            "session_progress": session.get_progress(),
        }

    def _pipeline_failed(
        self,
        reason: str,
        details: list,
        session: ApplicationSession,
        audit: AuditLogger,
    ) -> Dict[str, Any]:
        """Handle pipeline failure gracefully."""
        session.status = "failed"
        self.session_manager.update_session(session)

        console.print(Panel(
            f"[bold red]Pipeline Blocked[/bold red]\n"
            f"Reason: {reason}\n"
            + ("\n".join(f"• {d}" for d in details[:5]) if details else ""),
            title="❌ Governance Block"
        ))

        audit.log_error("orchestrator", "pipeline_start", f"{reason}: {details}")

        return {
            "success": False,
            "session_id": session.session_id,
            "error": reason,
            "details": details,
            "outputs": {},
            "evaluations": {},
            "output_files": {},
        }
