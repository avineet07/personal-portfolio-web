"""
config.py — Centralized configuration for the resume & cover letter pipeline.

Loads environment variables from .env and defines standard file/directory paths.
"""

import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Input Directories
REF_DIR = ROOT_DIR / "ref"
RESUME_DIR = REF_DIR / "resume"
COVER_LETTER_DIR = REF_DIR / "cover_letter"

# Output Locations
DATA_DIR = ROOT_DIR / "src" / "data"
DEFAULT_JSON_PATH = DATA_DIR / "portfolio_data.json"
CONTENT_DIR = ROOT_DIR / "content"
WORK_DIR = CONTENT_DIR / "work"
PROJECTS_DIR = CONTENT_DIR / "projects"

# LLM Configuration
USE_LLM = os.getenv("USE_LLM", "false").strip().lower() in ("true", "1", "yes")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

