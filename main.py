"""
main.py - Entry point for the Job Application Assistant
══════════════════════════════════════════════════════════
End-to-End Agentic Pipeline with Governance & Evaluation

Usage:
    python main.py
    python main.py --resume path/to/resume.txt --jd path/to/jd.txt --company "Google" --role "Software Engineer"
    python main.py --demo
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

console = Console()


# ─────────────────────────────────────────────────────────────────
# Demo Data (used when --demo flag is passed)
# ─────────────────────────────────────────────────────────────────

DEMO_RESUME = """
John Doe
john.doe@email.com | +1 (555) 123-4567 | San Francisco, CA | linkedin.com/in/johndoe | github.com/johndoe

PROFESSIONAL SUMMARY
Results-driven Software Engineer with 5 years of experience building scalable backend systems and cloud-native
applications. Passionate about distributed systems, machine learning infrastructure, and developer tooling.

TECHNICAL SKILLS
Languages : Python, Java, Go, TypeScript, SQL
Frameworks: FastAPI, Spring Boot, React, gRPC
Cloud      : AWS (EC2, S3, Lambda, RDS, SQS), Docker, Kubernetes, Terraform
Databases  : PostgreSQL, Redis, MongoDB, Cassandra
ML/AI      : TensorFlow, PyTorch, scikit-learn, Pandas, NumPy
Tools      : Git, Jenkins, GitHub Actions, Datadog, Prometheus

PROFESSIONAL EXPERIENCE

TechCorp Inc. | Senior Software Engineer | Jan 2022 – Present
• Designed and built a real-time data pipeline processing 10M events/day using Kafka and Apache Flink
• Reduced API latency by 40% by implementing Redis caching layer and database query optimization
• Led migration of 3 monolithic services to microservices architecture, improving deployment frequency by 3x
• Mentored 4 junior engineers and introduced code review standards adopted by the entire team
• Built CI/CD pipeline using GitHub Actions reducing deployment time from 2 hours to 15 minutes

DataFlow Systems | Software Engineer | Jun 2020 – Dec 2021
• Developed Python-based ETL pipelines processing $50M in financial transactions monthly
• Implemented ML model serving infrastructure using FastAPI and Docker, reducing model deployment time by 60%
• Collaborated with data science team to productionize 5 ML models, serving 200K+ users daily
• Improved database query performance by 35% through indexing strategy and query optimization

StartupXYZ | Junior Software Engineer | Aug 2019 – May 2020
• Built REST APIs using Django serving 50K daily active users
• Implemented automated testing suite increasing code coverage from 45% to 82%
• Contributed to React frontend, delivering 3 major product features on schedule

EDUCATION
B.S. Computer Science | University of California, Berkeley | 2019 | GPA: 3.7

CERTIFICATIONS
• AWS Certified Solutions Architect – Associate (2023)
• Google Cloud Professional Data Engineer (2022)

PROJECTS
• OpenSource MLOps Tool: Built a Kubernetes-native ML model monitoring tool (500+ GitHub stars)
• Distributed Cache Library: Python library for distributed caching patterns (PyPI: 10K+ downloads)
"""

DEMO_JOB_DESCRIPTION = """
Senior Software Engineer – AI Infrastructure
Google DeepMind | San Francisco, CA | Full-time

About the Role:
We're looking for a Senior Software Engineer to join our AI Infrastructure team. You'll design and build
the systems that power Google's next-generation AI research and products.

Responsibilities:
• Design, build, and operate large-scale distributed systems for ML training and inference
• Develop ML infrastructure tools and platforms used by 500+ researchers
• Collaborate with ML researchers to productionize models at Google scale
• Lead technical design reviews and mentor junior engineers
• Drive adoption of best practices in reliability, observability, and performance
• Build CI/CD pipelines and developer tooling for ML workflows

Required Qualifications:
• 4+ years of software engineering experience
• Strong proficiency in Python and Go (or C++)
• Experience with distributed systems, microservices architecture
• Experience with cloud platforms (GCP preferred, AWS/Azure acceptable)
• Experience with Kubernetes, Docker, and container orchestration
• Strong understanding of ML concepts and ML infrastructure (training, serving, monitoring)
• Experience with data pipelines and stream processing (Kafka, Flink, or similar)

Preferred Qualifications:
• Experience with MLOps tools and frameworks (Kubeflow, MLflow, or similar)
• Contributions to open-source ML infrastructure projects
• Experience with TensorFlow or PyTorch in production environments
• Publication record or research experience a plus

What We Offer:
• Competitive salary ($180K-$280K base + equity + benefits)
• Work on cutting-edge AI systems at massive scale
• Collaborative, research-driven culture
• Flexible work arrangements
"""

DEMO_COMPANY = "Google"
DEMO_ROLE = "Senior Software Engineer – AI Infrastructure"
DEMO_APPLICANT = "John Doe"


# ─────────────────────────────────────────────────────────────────
# Main Pipeline Runner
# ─────────────────────────────────────────────────────────────────

def run_pipeline(
    resume_text: str,
    job_description: str,
    company_name: str,
    target_role: str,
    applicant_name: str,
) -> dict:
    """Initialize and run the full pipeline."""
    from agents.orchestrator import JobApplicationOrchestrator

    orchestrator = JobApplicationOrchestrator()
    return orchestrator.run(
        resume_text=resume_text,
        job_description=job_description,
        company_name=company_name,
        target_role=target_role,
        applicant_name=applicant_name,
    )


def print_results(result: dict):
    """Print a beautiful summary of pipeline results."""
    if not result.get("success"):
        console.print(Panel(
            f"[bold red]Pipeline Failed[/bold red]\n{result.get('error', 'Unknown error')}",
            title="❌ Error"
        ))
        return

    console.print("\n")
    console.print(Panel(
        "[bold green]Pipeline Completed Successfully![/bold green]\n\n"
        "All outputs have been saved to the [cyan]outputs/[/cyan] directory.",
        title="🎉 Success"
    ))

    # Evaluation summary table
    evals = result.get("evaluations", {})
    table = Table(title="📊 Evaluation Scores", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white", width=20)
    table.add_column("Score", justify="center", width=10)
    table.add_column("Grade", justify="center", width=8)
    table.add_column("Status", justify="center", width=12)

    components = [
        ("Resume", "resume"),
        ("Cover Letter", "cover_letter"),
        ("Interview Prep", "interview_prep"),
    ]
    for label, key in components:
        eval_data = evals.get(key, {})
        score = eval_data.get("overall_score", 0)
        grade = eval_data.get("grade", "N/A")
        passed = eval_data.get("passed", False)
        status = "[green]✓ READY[/green]" if passed else "[yellow]⚠ REVISE[/yellow]"
        score_color = "green" if score >= 70 else "yellow" if score >= 55 else "red"
        table.add_row(label, f"[{score_color}]{score:.1f}/100[/{score_color}]", grade, status)

    console.print(table)

    # Output files table
    files = result.get("output_files", {})
    if files:
        file_table = Table(title="📁 Output Files", show_header=True, header_style="bold cyan")
        file_table.add_column("File Type", style="white", width=25)
        file_table.add_column("File Path", style="cyan")

        labels = {
            "tailored_resume": "Tailored Resume",
            "cover_letter": "Cover Letter",
            "interview_prep": "Interview Prep",
            "evaluation_report": "Evaluation Report",
            "session_data": "Session Data (JSON)",
        }
        for key, path in files.items():
            file_table.add_row(labels.get(key, key), path)
        console.print(file_table)

    # Governance summary
    gov = result.get("governance", {})
    audit = gov.get("audit_summary", {})
    if audit:
        console.print(Panel(
            f"Audit Events  : {audit.get('total_events', 0)}\n"
            f"Blocked       : {audit.get('blocked_count', 0)}\n"
            f"Errors        : {audit.get('error_count', 0)}\n"
            f"Health        : [{'green' if audit.get('pipeline_health') == 'HEALTHY' else 'yellow'}]"
            f"{audit.get('pipeline_health', 'N/A')}[/{'green' if audit.get('pipeline_health') == 'HEALTHY' else 'yellow'}]\n"
            f"Log File      : logs/audit.log",
            title="🛡️ Governance Summary"
        ))


def load_text_file(path: str) -> str:
    """Load text from a file."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def interactive_mode():
    """Run the pipeline in interactive CLI mode."""
    console.print(Panel(
        "[bold cyan]Job Application Assistant[/bold cyan]\n"
        "Powered by Multi-Agent AI + Governance + Evaluation",
        title="🤖 Welcome",
        subtitle="End-to-End Agentic Pipeline"
    ))

    console.print("\n[bold]Enter your information:[/bold]\n")

    # Collect inputs
    applicant_name = console.input("[cyan]Your Name[/cyan]: ").strip() or "Applicant"
    company_name = console.input("[cyan]Company Name[/cyan]: ").strip() or "Target Company"
    target_role = console.input("[cyan]Target Role[/cyan]: ").strip() or "Software Engineer"

    console.print("\n[cyan]Paste your resume text (press Enter twice when done):[/cyan]")
    lines = []
    empty_count = 0
    while empty_count < 2:
        line = input()
        if line == "":
            empty_count += 1
        else:
            empty_count = 0
            lines.append(line)
    resume_text = "\n".join(lines).strip()

    console.print("\n[cyan]Paste the job description (press Enter twice when done):[/cyan]")
    lines = []
    empty_count = 0
    while empty_count < 2:
        line = input()
        if line == "":
            empty_count += 1
        else:
            empty_count = 0
            lines.append(line)
    job_description = "\n".join(lines).strip()

    if not resume_text or not job_description:
        console.print("[red]Error: Resume and job description are required.[/red]")
        sys.exit(1)

    result = run_pipeline(resume_text, job_description, company_name, target_role, applicant_name)
    print_results(result)


def check_api_key():
    """Check if GOOGLE_API_KEY is set."""
    import os
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key or key == "your_google_api_key_here":
        console.print(Panel(
            "[bold red]GOOGLE_API_KEY not configured![/bold red]\n\n"
            "Steps to fix:\n"
            "1. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan]\n"
            "2. Get your API key from: [link]https://aistudio.google.com/app/apikey[/link]\n"
            "3. Set [cyan]GOOGLE_API_KEY=your_key[/cyan] in the [cyan].env[/cyan] file\n"
            "4. Run again!",
            title="⚠️ Configuration Required"
        ))
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Job Application Assistant — End-to-End Agentic AI Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --resume resume.txt --jd job.txt --company "Google" --role "ML Engineer"
  python main.py  (interactive mode)
        """
    )
    parser.add_argument("--demo", action="store_true", help="Run with built-in demo data")
    parser.add_argument("--resume", type=str, help="Path to resume file (txt, pdf, docx)")
    parser.add_argument("--jd", type=str, help="Path to job description file")
    parser.add_argument("--company", type=str, default="Target Company", help="Company name")
    parser.add_argument("--role", type=str, default="Software Engineer", help="Target role")
    parser.add_argument("--name", type=str, default="Applicant", help="Your name")
    parser.add_argument("--no-check", action="store_true", help="Skip API key check")

    args = parser.parse_args()

    # API key check
    if not args.no_check:
        check_api_key()

    if args.demo:
        # ── DEMO MODE ──────────────────────────────────────────────
        console.print(Panel(
            "[bold cyan]Running in DEMO mode[/bold cyan]\n"
            "Using built-in sample resume and Google job description",
            title="🎯 Demo Mode"
        ))
        result = run_pipeline(
            resume_text=DEMO_RESUME,
            job_description=DEMO_JOB_DESCRIPTION,
            company_name=DEMO_COMPANY,
            target_role=DEMO_ROLE,
            applicant_name=DEMO_APPLICANT,
        )
        print_results(result)

        # Show master report snippet in terminal
        master_report = result.get("outputs", {}).get("master_report", "")
        if master_report:
            console.print("\n[bold]Master Evaluation Report Preview:[/bold]")
            console.print(master_report[:3000] + "\n...[Saved to outputs/reports/ for full report]")

    elif args.resume and args.jd:
        # ── FILE MODE ─────────────────────────────────────────────
        resume_text = load_text_file(args.resume)

        # Handle PDF/DOCX
        if args.resume.endswith(".pdf") or args.resume.endswith(".docx"):
            from tools.pdf_tools import parse_pdf_resume
            parsed = parse_pdf_resume(args.resume)
            if not parsed.get("success"):
                console.print(f"[red]Failed to parse file: {parsed.get('error')}[/red]")
                sys.exit(1)
            resume_text = parsed["raw_text"]

        jd_text = load_text_file(args.jd)

        result = run_pipeline(
            resume_text=resume_text,
            job_description=jd_text,
            company_name=args.company,
            target_role=args.role,
            applicant_name=args.name,
        )
        print_results(result)

    else:
        # ── INTERACTIVE MODE ───────────────────────────────────────
        interactive_mode()


if __name__ == "__main__":
    main()
