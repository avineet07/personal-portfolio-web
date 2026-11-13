#!/usr/bin/env python3
r"""
scripts/run_pipeline.py — Command-line interface for the automated resume-to-portfolio pipeline.

Ingests documents from ref/resume/ and ref/cover_letter/ (or custom paths),
executes generic section generators (via LLM or deterministic parsing),
and compiles a clean static JSON (src/data/portfolio_data.json) to drive HTML templates.

Usage:
  python scripts/run_pipeline.py
  python scripts/run_pipeline.py --resume ref/resume/resume.pdf --cover-letter ref/cover_letter/cover_letter.pdf
  python scripts/run_pipeline.py --use-llm --provider gemini --scaffold-articles
  python scripts/run_pipeline.py --historical
"""

import os
import sys
import argparse
from pathlib import Path

# Resolve ROOT and src directory
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from pipeline import run_pipeline, DEFAULT_JSON_PATH, RESUME_DIR, COVER_LETTER_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Generic, Unbiased Resume & Cover Letter Pipeline for Personal Portfolio."
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=str(RESUME_DIR),
        help=f"Path or directory for the resume PDF (default: {RESUME_DIR})"
    )
    parser.add_argument(
        "--cover-letter",
        type=str,
        default=str(COVER_LETTER_DIR),
        help=f"Path or directory for the cover letter PDF (default: {COVER_LETTER_DIR})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_JSON_PATH),
        help=f"Destination static JSON path (default: {DEFAULT_JSON_PATH})"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        default=None,
        help="Enable LLM parsing (reads keys from .env). If omitted, runs generic heuristic extraction."
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["auto", "gemini", "openai", "anthropic", "offline"],
        help="LLM provider (default: from .env, or 'auto')"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optional API key override"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model name override"
    )
    parser.add_argument(
        "--scaffold-articles",
        action="store_true",
        help="Automatically generate contextual markdown case studies in content/work/ for roles without articles"
    )
    parser.add_argument(
        "--historical",
        action="store_true",
        help="Copy verified historical baseline (portfolio_data_historical.json) to portfolio_data.json"
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            resume_path=args.resume,
            cover_letter_path=args.cover_letter,
            output_json_path=args.output,
            use_llm=args.use_llm,
            provider=args.provider,
            api_key=args.api_key,
            model=args.model,
            auto_scaffold_articles=args.scaffold_articles,
            use_historical=args.historical
        )
        print("✨ Next Steps:")
        print("   • Start dev server: python app.py")
        print("   • Build static site: python scripts/build.py")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

