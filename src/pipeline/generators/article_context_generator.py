"""
article_context_generator.py — Cross-references resume experience with content articles.

Scans content/work and content/projects, identifies existing relevant articles,
and can scaffold contextual Markdown case studies for any role or technical initiative
in the resume that lacks a detailed article.
"""

import os
import re
from typing import List, Dict, Any, Optional
from ..llm_client import LLMClient

CONTENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "content"))
WORK_DIR = os.path.join(CONTENT_DIR, "work")
PROJECTS_DIR = os.path.join(CONTENT_DIR, "projects")


def enrich_article_context(
    experiences: List[Dict[str, Any]],
    llm_client: Optional[LLMClient] = None,
    auto_scaffold: bool = False
) -> Dict[str, Any]:
    """
    Matches experiences with content articles in content/work and content/projects.
    If auto_scaffold is True and a role has no matching case study, generates one.
    """
    existing_work_files = _list_markdown_files(WORK_DIR)
    existing_project_files = _list_markdown_files(PROJECTS_DIR)

    matched_work_cases = []
    scaffolded_cases = []

    for exp in experiences:
        company = exp.get("company", "").strip()
        matched = False
        for fpath in existing_work_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if company.lower() in content.lower():
                        matched = True
                        matched_work_cases.append({
                            "company": company,
                            "file": os.path.basename(fpath),
                            "path": fpath
                        })
            except Exception:
                continue

        # If not matched and auto_scaffold is requested, create a draft
        if not matched and auto_scaffold and company:
            new_file = _scaffold_case_study(exp, llm_client)
            if new_file:
                scaffolded_cases.append(new_file)

    return {
        "matched_work_count": len(matched_work_cases),
        "matched_work_cases": matched_work_cases,
        "scaffolded_cases": scaffolded_cases
    }


def _list_markdown_files(directory: str) -> List[str]:
    if not os.path.exists(directory):
        return []
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".md") and not f.startswith(".")
    ]


def _scaffold_case_study(exp: Dict[str, Any], llm_client: Optional[LLMClient] = None) -> Optional[str]:
    """Generates a contextual markdown case study for a role."""
    company = exp.get("company", "Company")
    role = exp.get("role", "Role")
    period = exp.get("period", "")
    slug = re.sub(r"[^a-z0-9]+", "-", f"{company}-{role}".lower()).strip("-")
    filename = f"90-{slug}.md"
    filepath = os.path.join(WORK_DIR, filename)

    if os.path.exists(filepath):
        return None

    bullets = exp.get("bullets", [])
    bullets_html = "\n".join([f"  <li>{b}</li>" for b in bullets])

    content = f"""---
id: {slug}
order: 90
title: "{role} Engineering & Architecture"
company: "{company}"
role: "{role}"
period: "{period}"
location: "{exp.get('location', '')}"
category: "{exp.get('category', 'Engineering & Analytics')}"
summary: "{exp.get('summary', '')}"
metrics:
  - "Architecture & Engineering"
  - "Business Impact"
techStack:
  - Python
  - SQL
---

<h3>Executive Summary</h3>
<p>{exp.get('summary', 'Engineered solutions delivering high-impact business outcomes.')}</p>

<h3>1. Technical Implementation</h3>
<ul>
{bullets_html}
</ul>

<h3>2. Key Impact</h3>
<p>Delivered measurable business improvements, improved architectural efficiency, and streamlined analytical workflows.</p>
"""
    try:
        os.makedirs(WORK_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"⚠️ Could not scaffold case study: {e}")
        return None

