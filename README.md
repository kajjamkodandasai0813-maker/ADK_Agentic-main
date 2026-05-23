<<<<<<< HEAD
# Job Application Assistant 🎯

An intelligent, multi-agent AI system built with Google's Agent Development Kit (ADK) that transforms the job application process through automation, personalization, and comprehensive evaluation.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Components](#components)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Governance & Safety](#governance--safety)
- [Evaluation System](#evaluation-system)

---

## 🎯 Overview

The Job Application Assistant is an end-to-end agentic pipeline that automates and enhances the job application process. It leverages multiple specialized AI agents, governance controls, and evaluation metrics to deliver high-quality, personalized job application materials.

### What It Does

1. **Parses** your resume to extract structured information
2. **Researches** the target company, role, and market trends
3. **Tailors** your resume to match the specific job description
4. **Generates** personalized, compelling cover letters
5. **Prepares** comprehensive interview materials (questions, answers, strategies)
6. **Evaluates** all outputs against quality metrics
7. **Exports** professional PDF/DOCX documents ready for submission

### Key Differentiators

- ✅ **Multi-Agent Architecture**: Specialized agents for each task
- ✅ **Governance Layer**: Input validation, content filtering, PII detection, rate limiting
- ✅ **Evaluation System**: Automated quality scoring and improvement suggestions
- ✅ **Session Memory**: Maintains context across the entire pipeline
- ✅ **Audit Trail**: Complete logging for transparency and debugging
- ✅ **Production-Ready**: Built with safety, error handling, and retry logic

---

## 🏗️ Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│  Resume (TXT/PDF/DOCX) + Job Description + Company + Role      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GOVERNANCE LAYER                              │
│  ├─ Input Validation (schema, file format, size)               │
│  ├─ Content Filtering (profanity, bias, toxicity)              │
│  ├─ PII Detection & Masking                                    │
│  ├─ Rate Limiting (per-user, per-session)                      │
│  └─ Audit Logging (all actions and decisions)                  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR                           │
│                  (Master Coordinator)                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│ Resume  │  │   Job    │  │ Resume   │
│ Parser  │─▶│Research  │─▶│ Tailor   │
│ Agent   │  │  Agent   │  │  Agent   │
└─────────┘  └──────────┘  └──────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        ┌──────────────┐              ┌────────────────┐
        │ Cover Letter │              │ Interview Prep │
        │    Agent     │              │     Agent      │
        └──────────────┘              └────────────────┘
                │                               │
                └───────────┬───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION LAYER                             │
│  ├─ Resume Evaluator (keyword match, ATS score, relevance)     │
│  ├─ Cover Letter Evaluator (personalization, tone, quality)    │
│  ├─ Interview Prep Evaluator (coverage, depth, relevance)      │
│  └─ Master Report Generator                                    │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                               │
│  ├─ Tailored Resume (PDF/DOCX)                                 │
│  ├─ Cover Letter (PDF/DOCX)                                    │
│  ├─ Interview Prep Guide (PDF/DOCX)                            │
│  ├─ Research Report (JSON)                                     │
│  └─ Evaluation Report (JSON)                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```
Orchestrator ──┬──► Resume Parser Agent
               │    └──► Structured Resume Data
               │
               ├──► Job Research Agent
               │    ├──► Company Intelligence
               │    ├──► Market Trends
               │    └──► Role Analysis
               │
               ├──► Resume Tailor Agent
               │    └──► Optimized Resume (keywords, achievements, structure)
               │
               ├──► Cover Letter Agent
               │    └──► Personalized Cover Letter
               │
               └──► Interview Prep Agent
                    ├──► Technical Questions & Answers
                    ├──► Behavioral Questions & STAR Answers
                    ├──► Company-Specific Questions
                    └──► Interview Strategy
```

---

## 📁 Directory Structure

```
job_application_assistant/
│
├── main.py                          # Entry point - CLI interface with demo mode
├── config.py                        # Central configuration (LLM, agents, governance)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
│
├── agents/                          # Multi-Agent System
│   ├── __init__.py
│   ├── base_agent.py               # Base class with LLM interface & retry logic
│   ├── orchestrator.py             # Master coordinator for pipeline
│   ├── resume_parser_agent.py      # Extracts structured data from resumes
│   ├── job_research_agent.py       # Company & market research
│   ├── resume_tailor_agent.py      # Optimizes resume for specific JD
│   ├── cover_letter_agent.py       # Generates personalized cover letters
│   └── interview_prep_agent.py     # Creates interview prep materials
│
├── governance/                      # Safety & Compliance Layer
│   ├── __init__.py
│   ├── input_validator.py          # Schema validation, sanity checks
│   ├── content_filter.py           # Profanity, bias, toxicity detection
│   ├── pii_detector.py             # Detects & masks sensitive information
│   ├── rate_limiter.py             # Token bucket rate limiting
│   └── audit_logger.py             # Immutable audit trail
│
├── evaluation/                      # Quality Assurance Layer
│   ├── __init__.py
│   ├── evaluator.py                # Master evaluator orchestrator
│   ├── resume_evaluator.py         # Resume vs JD match scoring
│   ├── cover_letter_evaluator.py   # Cover letter quality analysis
│   └── metrics.py                  # Scoring models & report generation
│
├── memory/                          # Session & State Management
│   ├── __init__.py
│   └── session_manager.py          # Tracks pipeline state & context
│
├── tools/                           # Utility Functions
│   ├── __init__.py
│   ├── file_tools.py               # File I/O, sanitization, export
│   ├── pdf_tools.py                # PDF generation & manipulation
│   └── search_tools.py             # Web scraping & search utilities
│
└── logs/                            # Generated at runtime
    └── audit.log                    # Complete audit trail
```

---

## 🧩 Components

### 1. **Agents** (`agents/`)

#### **Base Agent** (`base_agent.py`)
- Abstract base class for all specialized agents
- Provides standardized LLM interface (Gemini 2.0 Flash)
- Implements retry logic with exponential backoff
- Common logging and error handling

#### **Orchestrator** (`orchestrator.py`)
- Master coordinator that manages the complete pipeline
- Sequential execution with progress tracking
- Integrates governance checks at each step
- Aggregates results from all agents
- Generates final reports and exports files

#### **Resume Parser Agent** (`resume_parser_agent.py`)
- Extracts structured information from resumes (TXT/PDF/DOCX)
- Parses: contact info, summary, skills, experience, education, projects
- Handles multiple formats and layouts
- Output: JSON-structured resume data

#### **Job Research Agent** (`job_research_agent.py`)
- Researches target company (culture, values, recent news)
- Analyzes market trends and salary benchmarks
- Deep-dives into job description requirements
- Identifies key skills, qualifications, and keywords
- Output: Research report with actionable insights

#### **Resume Tailor Agent** (`resume_tailor_agent.py`)
- Optimizes resume for specific job description
- Keyword injection (ATS optimization)
- Re-prioritizes relevant experience and skills
- Quantifies achievements with metrics
- Output: Tailored resume text ready for formatting

#### **Cover Letter Agent** (`cover_letter_agent.py`)
- Generates personalized, compelling cover letters
- Research-driven (uses company intelligence)
- Storytelling approach with specific examples
- Professional tone with enthusiasm
- Output: Complete cover letter (3-4 paragraphs)

#### **Interview Prep Agent** (`interview_prep_agent.py`)
- Generates comprehensive interview materials:
  - Technical questions specific to the role
  - Behavioral questions with STAR-method answers
  - Company-specific questions
  - Questions to ask the interviewer
  - Overall interview strategy
- Output: Structured interview guide

### 2. **Governance** (`governance/`)

#### **Input Validator** (`input_validator.py`)
- Validates input schema and file formats
- File size and security checks
- Sanity checks (resume length, JD completeness)
- Prevents malformed or malicious inputs

#### **Content Filter** (`content_filter.py`)
- Detects profanity, bias, and toxic language
- Pattern-based and heuristic filtering
- Blocks or flags inappropriate content
- Configurable sensitivity levels

#### **PII Detector** (`pii_detector.py`)
- Identifies sensitive information (SSN, credit cards, etc.)
- Masks PII in logs and audit trails
- Regex-based pattern matching
- Protects user privacy

#### **Rate Limiter** (`rate_limiter.py`)
- Token bucket algorithm for rate limiting
- Per-user and per-session limits
- Prevents abuse and manages API costs
- Configurable limits and windows

#### **Audit Logger** (`audit_logger.py`)
- Immutable audit trail for all operations
- Records: agent calls, tool usage, governance decisions
- JSON-structured logs with timestamps
- Critical for compliance and debugging

### 3. **Evaluation** (`evaluation/`)

#### **Master Evaluator** (`evaluator.py`)
- Orchestrates all evaluation modules
- Aggregates scores into master report
- Tracks evaluation history
- Generates improvement suggestions

#### **Resume Evaluator** (`resume_evaluator.py`)
- Keyword match analysis (required vs. present)
- ATS compatibility scoring
- Quantification score (metrics in achievements)
- Relevance and completeness checks
- Output: Score (0-100) with detailed breakdown

#### **Cover Letter Evaluator** (`cover_letter_evaluator.py`)
- Personalization check (company/role mentions)
- Tone and professionalism analysis
- Structure and format validation
- Enthusiasm and authenticity scoring
- Output: Score (0-100) with feedback

#### **Metrics** (`metrics.py`)
- Data models for evaluation reports
- Score calculation algorithms
- Report generation utilities
- Performance tracking

### 4. **Memory** (`memory/`)

#### **Session Manager** (`session_manager.py`)
- Maintains pipeline state across execution
- Stores intermediate results and context
- Enables resume and retry capabilities
- Structured session data with timestamps

### 5. **Tools** (`tools/`)

#### **File Tools** (`file_tools.py`)
- Read/write operations for TXT/JSON files
- Path sanitization and validation
- Directory creation and management
- Cross-platform compatibility

#### **PDF Tools** (`pdf_tools.py`)
- PDF parsing (PyPDF2)
- PDF generation (ReportLab)
- Professional formatting for outputs
- DOCX support (python-docx)

#### **Search Tools** (`search_tools.py`)
- Web scraping utilities (BeautifulSoup)
- Company research APIs
- LinkedIn/Glassdoor data extraction (if available)
- Search result parsing

---

## ✨ Features

### Core Capabilities
- ✅ **Multi-format resume parsing** (TXT, PDF, DOCX)
- ✅ **AI-powered company research**
- ✅ **ATS-optimized resume tailoring**
- ✅ **Personalized cover letter generation**
- ✅ **Comprehensive interview preparation**
- ✅ **Automated quality evaluation**

### Governance & Safety
- ✅ **Input validation and sanitization**
- ✅ **Content filtering (profanity, bias, toxicity)**
- ✅ **PII detection and masking**
- ✅ **Rate limiting and abuse prevention**
- ✅ **Complete audit trail**

### User Experience
- ✅ **Rich CLI with progress tracking**
- ✅ **Demo mode for testing**
- ✅ **Multiple output formats (PDF, DOCX, JSON)**
- ✅ **Detailed evaluation reports**
- ✅ **Error handling and retry logic**

### Technical Excellence
- ✅ **Modular architecture (easy to extend)**
- ✅ **Type hints and documentation**
- ✅ **Exception handling and logging**
- ✅ **Configurable via environment variables**
- ✅ **Production-ready code quality**

---

## 🚀 Installation

### Prerequisites
- Python 3.9+
- Google AI Studio API Key ([Get it here](https://makersuite.google.com/app/apikey))

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd job_application_assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API key
   GOOGLE_API_KEY=your_api_key_here
   MODEL_NAME=gemini-2.0-flash
   TEMPERATURE=0.3
   MAX_OUTPUT_TOKENS=8192
   ```

---

## 💻 Usage

### Demo Mode (Quick Test)

Test the system with built-in demo data:

```bash
python main.py --demo
```

This runs the complete pipeline with sample resume and job description.

### Standard Usage

```bash
python main.py \
  --resume path/to/your/resume.txt \
  --jd path/to/job_description.txt \
  --company "Google" \
  --role "Software Engineer"
```

### Advanced Usage

```bash
python main.py \
  --resume ~/Documents/resume.pdf \
  --jd ~/Downloads/job_posting.txt \
  --company "OpenAI" \
  --role "Machine Learning Engineer" \
  --output-dir ./applications/openai_ml_engineer
```

### Command-Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--resume` | Yes* | Path to your resume (TXT/PDF/DOCX) | Demo resume |
| `--jd` | Yes* | Path to job description | Demo JD |
| `--company` | Yes* | Target company name | Demo company |
| `--role` | Yes* | Target role/position | Demo role |
| `--output-dir` | No | Directory for output files | `./output` |
| `--demo` | No | Run demo mode with sample data | False |

*Required unless `--demo` is used

### Output Files

After successful execution, you'll find:

```
output/
├── tailored_resume.txt                # Optimized resume
├── tailored_resume.pdf                # Professional PDF format
├── cover_letter.txt                   # Personalized cover letter
├── cover_letter.pdf                   # Professional PDF format
├── interview_prep.txt                 # Interview guide
├── interview_prep.pdf                 # Professional PDF format
├── research_report.json               # Company research data
├── evaluation_report.json             # Quality scores and feedback
└── session_data.json                  # Complete pipeline state
```

---

## ⚙️ Configuration

### LLM Configuration (`config.py`)

```python
# Model Selection
MODEL_NAME = "gemini-2.0-flash"        # Use Gemini 2.0 Flash for speed
# MODEL_NAME = "gemini-1.5-pro"       # Use for higher quality (slower)

# Generation Parameters
TEMPERATURE = 0.3                      # Lower = more deterministic
MAX_OUTPUT_TOKENS = 8192               # Maximum response length
```

### Agent Configuration

Each agent can be configured independently:

```python
AGENT_CONFIG = {
    "orchestrator": {
        "max_iterations": 10,
    },
    "resume_parser": {
        "max_iterations": 3,
    },
    # ... more agents
}
```

### Governance Configuration

```python
GOVERNANCE_CONFIG = {
    "enable_input_validation": True,
    "enable_content_filtering": True,
    "enable_pii_detection": True,
    "enable_rate_limiting": True,
    "enable_audit_logging": True,
    
    "content_filter": {
        "block_profanity": True,
        "detect_bias": True,
        "toxicity_threshold": 0.7,
    },
    
    "rate_limiter": {
        "requests_per_minute": 10,
        "max_burst": 5,
    },
}
```

### Evaluation Configuration

```python
EVALUATION_CONFIG = {
    "enable_evaluation": True,
    "score_thresholds": {
        "excellent": 90,
        "good": 75,
        "acceptable": 60,
        "needs_improvement": 0,
    },
}
```

---

## 🛡️ Governance & Safety

### Input Validation
- File format checks (TXT, PDF, DOCX)
- File size limits (default: 10MB)
- Resume length validation (must be 100+ words)
- Job description completeness check

### Content Filtering
- Profanity detection (blocks offensive language)
- Bias detection (flags discriminatory content)
- Toxicity analysis (measures harmful language)

### PII Protection
- Detects: SSN, credit cards, passport numbers, etc.
- Masks sensitive data in logs: `SSN: ***-**-1234`
- Never stores raw PII in audit logs

### Rate Limiting
- Default: 10 requests/minute per user
- Token bucket algorithm
- Prevents API abuse and manages costs

### Audit Logging
Every operation is logged:
```json
{
  "event_id": "evt_001",
  "timestamp": "2026-03-31T10:15:30Z",
  "event_type": "AGENT_CALL",
  "agent_name": "ResumeTailorAgent",
  "action": "tailor_resume",
  "status": "SUCCESS",
  "duration_ms": 3450.2,
  "governance_flags": []
}
```

---

## 📊 Evaluation System

### Resume Evaluation

**Dimensions:**
- **Keyword Match**: Required skills present in resume (0-100)
- **ATS Score**: Applicant Tracking System compatibility (0-100)
- **Quantification**: Use of metrics and numbers (0-100)
- **Relevance**: Experience relevance to role (0-100)

**Output:**
```json
{
  "overall_score": 87,
  "dimensions": {
    "keyword_match": 92,
    "ats_score": 85,
    "quantification": 88,
    "relevance": 83
  },
  "feedback": [
    "Excellent keyword coverage (92%)",
    "Consider adding more metrics to achievements",
    "Strong alignment with job requirements"
  ]
}
```

### Cover Letter Evaluation

**Dimensions:**
- **Personalization**: Company/role-specific content (0-100)
- **Tone**: Professionalism and enthusiasm (0-100)
- **Structure**: Proper format and flow (0-100)
- **Authenticity**: Genuine voice, not generic (0-100)

### Interview Prep Evaluation

**Dimensions:**
- **Coverage**: Breadth of question types (0-100)
- **Depth**: Quality of answers (0-100)
- **Relevance**: Alignment with role/company (0-100)

---

## 🔧 Troubleshooting

### Common Issues

**Issue: API Key Error**
```
Error: GOOGLE_API_KEY not found
```
**Solution:** Ensure you've created a `.env` file with your API key.

**Issue: File Not Found**
```
Error: Resume file not found
```
**Solution:** Use absolute paths or verify relative path from current directory.

**Issue: PDF Parsing Fails**
```
Error: Could not parse PDF
```
**Solution:** Try converting to TXT or DOCX. Some PDFs have image-based text.

**Issue: Rate Limit Exceeded**
```
Error: Rate limit exceeded
```
**Solution:** Wait 60 seconds or adjust `GOVERNANCE_CONFIG` rate limits.

---

## 🛠️ Development

### Adding a New Agent

1. Create new file: `agents/your_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Register in `config.py`
5. Add to orchestrator pipeline

### Adding a New Governance Check

1. Create new file: `governance/your_check.py`
2. Implement check logic
3. Integrate into orchestrator gate
4. Configure in `config.py`

### Adding a New Evaluation Dimension

1. Update `evaluation/metrics.py` with new dimension
2. Add scoring logic to relevant evaluator
3. Update report generation

---

## 📄 License

This project is for educational purposes. Ensure compliance with all applicable laws and API terms of service.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional output formats (LaTeX, HTML)
- Integration with LinkedIn/Indeed/Glassdoor APIs
- Multi-language support
- Advanced NLP evaluation metrics
- Web UI/dashboard
- Batch processing for multiple applications

---

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review audit logs: `logs/audit.log`
3. Enable debug mode in `config.py`

---

## 🎓 Built With

- [Google Gemini 2.0](https://deepmind.google/technologies/gemini/) - LLM Foundation
- [Google ADK](https://github.com/google/adk) - Agent Development Kit
- [PyPDF2](https://pypdf2.readthedocs.io/) - PDF Processing
- [ReportLab](https://www.reportlab.com/) - PDF Generation
- [Rich](https://rich.readthedocs.io/) - CLI Interface
- [Pydantic](https://docs.pydantic.dev/) - Data Validation

---

**Made with ❤️ and AI**

*Transform your job applications from manual drudgery to automated excellence.*
=======
# ADK_Agentic
>>>>>>> 696d9c02eab0f38eaf229a03112f5067d83da955
