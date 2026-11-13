"""
coordinator.py — Central orchestrator for the resume & cover letter to portfolio pipeline.

Ingests documents from ref/resume/ and ref/cover_letter/ (or custom paths),
executes generic section generators (via LLM when enabled, or via generic heuristic parsing),
and compiles a clean, human-editable static JSON file (src/data/portfolio_data.json)
to power the portfolio website templates.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from .config import (
    DEFAULT_JSON_PATH,
    RESUME_DIR,
    COVER_LETTER_DIR,
    USE_LLM,
    LLM_PROVIDER,
    LLM_MODEL,
)
from .pdf_extractor import (
    extract_resume_document,
    extract_cover_letter_document,
)
from .llm_client import LLMClient
from .section_splitter import (
    split_resume_into_sections,
    GroundingContext,
)
from .generators.profile_generator import generate_profile
from .generators.pillars_generator import generate_pillars
from .generators.experience_generator import generate_experience
from .generators.education_generator import generate_education_and_internships
from .generators.article_context_generator import enrich_article_context


def run_pipeline(
    resume_path: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
    output_json_path: Optional[str] = None,
    use_llm: Optional[bool] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    auto_scaffold_articles: bool = False,
    use_historical: bool = False
) -> Dict[str, Any]:
    """
    Executes the end-to-end document parsing and portfolio compilation pipeline.
    """
    out_path = Path(output_json_path) if output_json_path else DEFAULT_JSON_PATH
    enable_llm = use_llm if use_llm is not None else USE_LLM

    print("\n🚀 Running Portfolio Generation Pipeline")
    print(f"   Output Target: {out_path}")
    print(f"   Mode: {'Historical Archive Copy' if use_historical else ('LLM Synthesis (' + (provider or LLM_PROVIDER) + ')' if enable_llm else 'Generic Deterministic Extraction')}")

    from data.loader import get_fallback_portfolio
    historical_data = get_fallback_portfolio()

    # If explicitly requesting historical baseline
    if use_historical:
        print("   ✓ Writing historical archived baseline to portfolio_data.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(historical_data, f, indent=2, ensure_ascii=False)
        return historical_data

    # Step 1: Ingest documents from ref/resume and ref/cover_letter
    resume_doc = extract_resume_document(resume_path)
    if not resume_doc:
        print(f"   ⚠️ No resume PDF found at '{resume_path or RESUME_DIR}'. Using historical baseline.")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(historical_data, f, indent=2, ensure_ascii=False)
        return historical_data

    resume_text = resume_doc["full_text"]
    source_resume = resume_doc["filename"]
    print(f"   ✓ Ingested Resume: {source_resume} ({resume_doc['page_count']} pages, {len(resume_text)} chars)")

    cover_letter_doc = extract_cover_letter_document(cover_letter_path)
    if cover_letter_doc:
        source_cover_letter = cover_letter_doc["filename"]
        cover_letter_text = cover_letter_doc["full_text"]
        print(f"   ✓ Ingested Cover Letter: {source_cover_letter} ({len(cover_letter_text)} chars)")
    else:
        source_cover_letter = None
        cover_letter_text = ""

    # Step 2: Initialize LLM Client (or offline heuristic engine)
    llm = LLMClient(provider=provider, api_key=api_key, model=model, enabled=enable_llm)
    print(f"   ✓ Extraction Engine: {llm.active_provider}")

    # Step 3: Hierarchical Resume Parsing & Grounding Construction
    sections = split_resume_into_sections(resume_text)
    active_sections = [k for k, v in sections.items() if v and k != "raw_text"]
    print(f"   ✓ Hierarchical Sections Identified: {', '.join(active_sections)}")

    # Load existing content articles for domain grounding & verification
    content_articles = []
    try:
        from src.content import load_work_cases, load_blogs
        content_articles = (load_work_cases() or []) + (load_blogs() or [])
    except Exception:
        pass

    grounding = GroundingContext(
        cover_letter=cover_letter_text,
        source_documents={
            "resume": source_resume,
            "cover_letter": source_cover_letter
        },
        content_articles=content_articles
    )

    # Step 4: Execute Section Generators on Isolated Slices
    print("   ... Extracting Profile Identity & Skills Matrix (Header, Summary, Skills)")
    profile = generate_profile(sections, llm, grounding=grounding)

    print("   ... Synthesizing Core Architectural Pillars (Domain & Skills Synthesis)")
    pillars = generate_pillars(sections, llm, grounding=grounding)

    print("   ... Parsing Professional Experience & Role Summaries (Experience Slice)")
    experiences = generate_experience(sections, llm, grounding=grounding)

    print("   ... Parsing Education & Internships (Education & Internships Slices)")
    edu_intern = generate_education_and_internships(sections, llm, grounding=grounding)

    print("   ... Cross-referencing Content Articles & Context")
    content_meta = enrich_article_context(
        experiences,
        llm,
        auto_scaffold=auto_scaffold_articles
    )

    # Step 5: Assemble Canonical Webpage-Friendly JSON Structure
    candidate_name = profile.get("name") or "Professional Portfolio"
    candidate_headline = profile.get("headline") or "AI/ML, Data Science & Engineering Professional"

    title = f"{candidate_name} | Data Science & Engineering Portfolio"
    meta_description = f"Portfolio and case studies of {candidate_name}, {candidate_headline}."

    resume_data = {
        "introduction": profile.get("introduction", ""),
        "headline": candidate_headline,
        "pillars": pillars,
        "workExperience": experiences,
        "internships": edu_intern.get("internships", []),
        "education": edu_intern.get("education", []),
        "title": title,
        "meta_description": meta_description,
    }

    portfolio_data = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_documents": {
            "resume": source_resume,
            "cover_letter": source_cover_letter
        },
        "profile": profile,
        "resume": resume_data,
        "content_meta": content_meta
    }

    # Step 5: Save to static JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(portfolio_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully compiled webpage-friendly portfolio data to: {out_path}\n")
    return portfolio_data
