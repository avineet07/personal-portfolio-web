"""
pdf_extractor.py — PDF text and document extraction for resumes and cover letters.

Handles file and directory resolution, extracting clean text from any PDF using
pypdf (with fallbacks to pdfplumber or pymupdf).
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import RESUME_DIR, COVER_LETTER_DIR


def resolve_pdf_path(path_or_dir: Optional[str], default_dir: Path) -> Optional[str]:
    """
    Resolves a PDF file path from a path or directory.
    If a directory is given, picks the latest modified .pdf file inside it.
    """
    if not path_or_dir:
        target = default_dir
    else:
        target = Path(path_or_dir)

    if not target.exists():
        return None

    if target.is_file() and target.suffix.lower() == ".pdf":
        return str(target)

    if target.is_dir():
        pdf_files = sorted(
            [f for f in target.glob("*.pdf") if not f.name.startswith(".")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if pdf_files:
            return str(pdf_files[0])

    return None


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts raw text and metadata from a PDF file.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages_text: List[str] = []

    # Try pypdf first
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            txt = page.extract_text() or ""
            pages_text.append(txt)
    except Exception as e_pypdf:
        # Fallback to pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    pages_text.append(txt)
        except Exception as e_pdfplumber:
            # Fallback to pymupdf
            try:
                import pymupdf
                doc = pymupdf.open(pdf_path)
                for page in doc:
                    pages_text.append(page.get_text())
            except Exception as e_fitz:
                raise RuntimeError(
                    f"Failed to extract PDF text. pypdf error: {e_pypdf}, "
                    f"pdfplumber error: {e_pdfplumber}, pymupdf error: {e_fitz}"
                )

    full_text = "\n".join(pages_text).strip()
    return {
        "filename": os.path.basename(pdf_path),
        "filepath": pdf_path,
        "page_count": len(pages_text),
        "full_text": full_text,
        "pages": pages_text
    }


def extract_resume_document(path_or_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Extracts text and metadata for the resume from ref/resume/ or a specified path."""
    resolved = resolve_pdf_path(path_or_dir, RESUME_DIR)
    if not resolved:
        return None
    return extract_text_from_pdf(resolved)


def extract_cover_letter_document(path_or_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Extracts text and metadata for the cover letter from ref/cover_letter/ or a specified path."""
    resolved = resolve_pdf_path(path_or_dir, COVER_LETTER_DIR)
    if not resolved:
        return None
    return extract_text_from_pdf(resolved)
