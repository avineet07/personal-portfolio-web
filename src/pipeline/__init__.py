"""
Pipeline package — automated resume & cover letter extraction, LLM synthesis, and JSON compilation.
"""

from .coordinator import run_pipeline
from .config import DEFAULT_JSON_PATH, RESUME_DIR, COVER_LETTER_DIR
from .pdf_extractor import (
    extract_text_from_pdf,
    extract_resume_document,
    extract_cover_letter_document,
)
from .section_splitter import (
    split_resume_into_sections,
    GroundingContext,
)
from .llm_client import LLMClient

__all__ = [
    "run_pipeline",
    "extract_text_from_pdf",
    "extract_resume_document",
    "extract_cover_letter_document",
    "split_resume_into_sections",
    "GroundingContext",
    "LLMClient",
    "DEFAULT_JSON_PATH",
    "RESUME_DIR",
    "COVER_LETTER_DIR",
]
