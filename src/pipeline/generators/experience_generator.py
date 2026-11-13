"""
experience_generator.py — Generic, unbiased extraction of professional work experience.

Extracts professional roles, organizations, timelines, bullets, and synthesizes
card preview summaries using insightful LLM prompts or generic heuristic parsing.
Contains zero hardcoded companies or institutional biases.
"""

import re
from typing import List, Dict, Any, Optional, Union
from ..llm_client import LLMClient
from ..section_splitter import resolve_sections_and_grounding, GroundingContext


def generate_experience(
    resume_input: Union[str, Dict[str, str]],
    llm_client: Optional[LLMClient] = None,
    grounding: Optional[Union[GroundingContext, Dict[str, Any], str]] = None
) -> List[Dict[str, Any]]:
    """
    Extracts work experience entries with roles, organizations, dates, bullets, and summaries.
    Operates on the pre-split hierarchical Experience section, grounded with cover letter context.
    """
    sections, g_ctx = resolve_sections_and_grounding(resume_input, grounding)
    exp_text = sections.get("experience") or sections.get("raw_text", "")
    grounding_notes = g_ctx.get_grounding_summary()

    if llm_client and llm_client.active_provider != "offline":
        grounding_section = ""
        if grounding_notes:
            grounding_section = f"\nGROUNDING & VERIFICATION CONTEXT (Do not invent employers or roles):\n\"\"\"\n{grounding_notes}\n\"\"\"\n"

        prompt = f"""
You are a Principal Engineering Recruiter and Executive Technical Portfolio Architect.
Analyze the following isolated Work Experience section from the candidate's resume.
{grounding_section}
For every role, produce an insightful, webpage-ready entry with this exact JSON schema:
[
  {{
    "role": "Official Job Title",
    "company": "Organization / Company Name",
    "location": "City, Country (or empty string)",
    "period": "Start Date – End Date (e.g. May 2024 – Present)",
    "category": "High-signal domain category (e.g. AI/ML & LLMs, Distributed Systems, Product Analytics)",
    "summary": "1-2 sentence high-impact executive summary for card preview highlighting primary architectural focus and measurable outcomes.",
    "bullets": [
      "Faithful, high-signal bullet point preserving technical architectures and metrics...",
      "..."
    ]
  }}
]

CRITICAL GROUNDING DIRECTIVES:
1. Extract positions ONLY from the provided text. Never invent employers, dates, or titles.
2. Maintain verified numerical metrics verbatim (e.g. percentages, speedups, latency). Never inflate or fabricate numbers.
3. If location or category is unspecified, infer category accurately from tools and responsibilities, or leave location empty.

Work Experience Section Text:
\"\"\"
{exp_text}
\"\"\"
"""
        result = llm_client.generate_json(
            prompt,
            system_instruction=(
                "You are an expert technical portfolio builder. "
                "Structure real resume data into professional, polished JSON entries without any hallucination."
            )
        )
        if result and isinstance(result, list) and len(result) > 0:
            return result
        if result and isinstance(result, dict) and "workExperience" in result:
            return result["workExperience"]

    # Generic Heuristic Fallback (completely unbiased)
    return _extract_experience_generic(exp_text)


def _extract_experience_generic(text: str) -> List[Dict[str, Any]]:
    """
    Generic heuristic parser that partitions work experience by dates and company/title boundaries
    without any hardcoded company names.
    """
    # 1. Isolate the Work Experience section
    exp_section = ""
    section_match = re.search(
        r"(?:WORK EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE)\s*\n+(.*?)(?=\n+(?:EDUCATION|TECHNICAL SKILLS|SKILLS|PROJECTS|INTERNSHIPS|CERTIFICATIONS)\b|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    exp_section = section_match.group(1) if section_match else text

    # Standard date range regex (e.g., "May 2024 – Present", "Jan 2021 – May 2024", "2019 – 2020", "05/2020 - 08/2022")
    date_regex = (
        r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|\d{1,2}/\d{4})"
        r"\s*[\u2013\u2014\-–]\s*"
        r"(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|\d{1,2}/\d{4})"
    )

    lines = [line.strip() for line in exp_section.split("\n") if line.strip()]
    if not lines:
        return []

    # Find line indices that contain date ranges
    job_indices = []
    for idx, line in enumerate(lines):
        if re.search(date_regex, line, re.IGNORECASE):
            job_indices.append(idx)

    experiences: List[Dict[str, Any]] = []

    for i, start_idx in enumerate(job_indices):
        end_idx = job_indices[i + 1] if i + 1 < len(job_indices) else len(lines)
        job_lines = lines[start_idx:end_idx]
        if not job_lines:
            continue

        header_line = job_lines[0]
        date_match = re.search(date_regex, header_line, re.IGNORECASE)
        period = date_match.group(0).strip() if date_match else "Dates"

        # The line containing the date often has the title before the date
        title_part = header_line[:date_match.start()].strip() if date_match else header_line
        title = title_part if title_part else "Role"

        # The next line often contains Company and Location (e.g. "Sears Holdings, Hyderabad, India")
        company = "Organization"
        location = ""
        body_start = 1

        if len(job_lines) > 1 and not job_lines[1].startswith(("•", "-", "*", "–")):
            comp_loc = job_lines[1]
            parts = [p.strip() for p in comp_loc.split(",") if p.strip()]
            if parts:
                company = parts[0]
                location = ", ".join(parts[1:]) if len(parts) > 1 else ""
            body_start = 2

        # Extract bullets
        bullets = []
        for line in job_lines[body_start:]:
            # If line is a category label like "AI/ML & Analytics" or "Data Engineering", note it
            if line.startswith(("•", "-", "*", "–")):
                clean_bullet = re.sub(r"^[•\-\*–]\s*", "", line).strip()
                if clean_bullet:
                    bullets.append(clean_bullet)
            elif len(line) > 30:
                bullets.append(line)

        # Dynamic category determination based on keywords
        combined_text = " ".join(job_lines).lower()
        if any(k in combined_text for k in ["langgraph", "llm", "agent", "deep learning", "nlp", "ai"]):
            category = "AI/ML & Analytics"
        elif any(k in combined_text for k in ["snowflake", "cdc", "pipeline", "etl", "dbt", "data warehouse"]):
            category = "Data Platform Engineering"
        elif any(k in combined_text for k in ["product", "churn", "lightgbm", "retention", "a/b test"]):
            category = "Product & ML"
        elif any(k in combined_text for k in ["risk", "credit", "consulting", "dashboard"]):
            category = "Risk Analytics"
        else:
            category = "Engineering & Analytics"

        # Formulate executive summary from bullets
        summary = ""
        if bullets:
            first_sentence = bullets[0].split(". ")[0].strip()
            summary = first_sentence if first_sentence.endswith(".") else f"{first_sentence}."
        else:
            summary = f"Key contributor at {company} executing engineering and analytical deliverables."

        experiences.append({
            "role": title,
            "company": company,
            "location": location,
            "period": period,
            "category": category,
            "summary": summary,
            "bullets": bullets
        })

    return experiences
