"""
tools/file_tools.py - File read/write operations for the job application pipeline
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import OUTPUT_CONFIG


def read_text_file(file_path: str) -> dict:
    """
    Read a plain text file (resume or job description).

    Args:
        file_path: Absolute or relative path to the text file

    Returns:
        dict with keys: success, content, file_name, char_count, error
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "content": "", "error": f"File not found: {file_path}"}

        if path.suffix.lower() not in [".txt", ".md"]:
            return {"success": False, "content": "", "error": f"Unsupported file type: {path.suffix}"}

        content = path.read_text(encoding="utf-8")
        return {
            "success": True,
            "content": content,
            "file_name": path.name,
            "char_count": len(content),
            "error": None,
        }
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


def write_text_file(file_name: str, content: str, sub_folder: str = "") -> dict:
    """
    Write output content to the outputs directory.

    Args:
        file_name: Name of the output file (e.g., 'tailored_resume.txt')
        content: The text content to write
        sub_folder: Optional sub-folder inside outputs/

    Returns:
        dict with keys: success, file_path, error
    """
    try:
        base_dir = Path(OUTPUT_CONFIG["output_dir"])
        if sub_folder:
            base_dir = base_dir / sub_folder
        base_dir.mkdir(parents=True, exist_ok=True)

        # Add timestamp to avoid overwrites
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(file_name).stem
        suffix = Path(file_name).suffix or ".txt"
        final_name = f"{stem}_{timestamp}{suffix}"
        file_path = base_dir / final_name

        file_path.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "file_path": str(file_path),
            "file_name": final_name,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "file_path": "", "error": str(e)}


def write_json_file(file_name: str, data: dict, sub_folder: str = "") -> dict:
    """
    Write structured data as JSON to the outputs directory.

    Args:
        file_name: Name of the JSON file
        data: Dictionary to serialize
        sub_folder: Optional sub-folder inside outputs/

    Returns:
        dict with keys: success, file_path, error
    """
    try:
        base_dir = Path(OUTPUT_CONFIG["output_dir"])
        if sub_folder:
            base_dir = base_dir / sub_folder
        base_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(file_name).stem
        final_name = f"{stem}_{timestamp}.json"
        file_path = base_dir / final_name

        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {
            "success": True,
            "file_path": str(file_path),
            "file_name": final_name,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "file_path": "", "error": str(e)}


def list_output_files(sub_folder: str = "") -> dict:
    """
    List all files generated in the outputs directory.

    Args:
        sub_folder: Optional sub-folder to list

    Returns:
        dict with keys: success, files (list), error
    """
    try:
        base_dir = Path(OUTPUT_CONFIG["output_dir"])
        if sub_folder:
            base_dir = base_dir / sub_folder

        if not base_dir.exists():
            return {"success": True, "files": [], "error": None}

        files = [
            {
                "name": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
            for f in base_dir.iterdir()
            if f.is_file()
        ]
        return {"success": True, "files": files, "count": len(files), "error": None}
    except Exception as e:
        return {"success": False, "files": [], "error": str(e)}
