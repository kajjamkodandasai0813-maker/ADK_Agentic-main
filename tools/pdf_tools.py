"""
tools/pdf_tools.py - PDF and DOCX resume parsing tools
"""

import re
from pathlib import Path
from typing import Optional


def parse_pdf_resume(file_path: str) -> dict:
    """
    Parse a PDF resume and extract raw text.

    Args:
        file_path: Path to the PDF file

    Returns:
        dict with: success, raw_text, page_count, error
    """
    try:
        import PyPDF2

        path = Path(file_path)
        if not path.exists():
            return {"success": False, "raw_text": "", "error": f"File not found: {file_path}"}

        if path.suffix.lower() == ".pdf":
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text.strip())
                raw_text = "\n\n".join(pages)

            return {
                "success": True,
                "raw_text": raw_text,
                "page_count": len(reader.pages),
                "char_count": len(raw_text),
                "file_name": path.name,
                "error": None,
            }

        elif path.suffix.lower() == ".docx":
            return parse_docx_resume(file_path)

        elif path.suffix.lower() == ".txt":
            raw_text = path.read_text(encoding="utf-8")
            return {
                "success": True,
                "raw_text": raw_text,
                "page_count": 1,
                "char_count": len(raw_text),
                "file_name": path.name,
                "error": None,
            }

        else:
            return {
                "success": False,
                "raw_text": "",
                "error": f"Unsupported format: {path.suffix}. Use PDF, DOCX, or TXT.",
            }

    except ImportError:
        return {
            "success": False,
            "raw_text": "",
            "error": "PyPDF2 not installed. Run: pip install PyPDF2",
        }
    except Exception as e:
        return {"success": False, "raw_text": "", "error": str(e)}


def parse_docx_resume(file_path: str) -> dict:
    """
    Parse a DOCX resume and extract raw text.

    Args:
        file_path: Path to the DOCX file

    Returns:
        dict with: success, raw_text, paragraph_count, error
    """
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        raw_text = "\n".join(paragraphs)

        return {
            "success": True,
            "raw_text": raw_text,
            "paragraph_count": len(paragraphs),
            "char_count": len(raw_text),
            "file_name": Path(file_path).name,
            "error": None,
        }
    except ImportError:
        return {
            "success": False,
            "raw_text": "",
            "error": "python-docx not installed. Run: pip install python-docx",
        }
    except Exception as e:
        return {"success": False, "raw_text": "", "error": str(e)}


def extract_resume_sections(raw_text: str) -> dict:
    """
    Extract structured sections from raw resume text using pattern matching.

    Args:
        raw_text: The raw text extracted from a resume

    Returns:
        dict with sections: contact, summary, skills, experience, education, certifications, projects
    """
    sections = {
        "contact": "",
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "certifications": "",
        "projects": "",
        "other": "",
    }

    # Section header patterns
    section_patterns = {
        "summary": r"(summary|objective|profile|about me|professional summary)",
        "skills": r"(skills|technical skills|core competencies|expertise|technologies)",
        "experience": r"(experience|work experience|employment|work history|professional experience)",
        "education": r"(education|academic|qualifications|degrees)",
        "certifications": r"(certifications?|licenses?|credentials|awards)",
        "projects": r"(projects?|personal projects?|portfolio|open source)",
        "contact": r"(contact|contact information|personal details)",
    }

    lines = raw_text.split("\n")
    current_section = "contact"
    section_content = {k: [] for k in sections}

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Check if this line is a section header
        matched_section = None
        for section, pattern in section_patterns.items():
            if re.match(pattern, line_clean.lower()):
                matched_section = section
                break

        if matched_section:
            current_section = matched_section
        else:
            section_content[current_section].append(line_clean)

    # Join sections
    for key in sections:
        sections[key] = "\n".join(section_content[key]).strip()

    # Extract contact info from top of resume (first 5 lines)
    if not sections["contact"]:
        top_lines = [l.strip() for l in lines[:8] if l.strip()]
        sections["contact"] = "\n".join(top_lines)

    # Extract emails and phones from raw text
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", raw_text)
    phones = re.findall(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", raw_text)

    return {
        "success": True,
        "sections": sections,
        "extracted_emails": emails,
        "extracted_phones": phones,
        "total_sections_found": sum(1 for v in sections.values() if v),
    }
