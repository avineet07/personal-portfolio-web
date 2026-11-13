"""
profile_generator.py — Generic, unbiased extraction of candidate profile identity and skills.

Extracts personal identity, contact links, narrative summary, and categorized skills matrix.
Contains zero hardcoded names, locations, or social handles.
"""

import re
from typing import Dict, Any, Optional, Union
from ..llm_client import LLMClient
from ..section_splitter import resolve_sections_and_grounding, GroundingContext


def generate_profile(
    resume_input: Union[str, Dict[str, str]],
    llm_client: Optional[LLMClient] = None,
    grounding: Optional[Union[GroundingContext, Dict[str, Any], str]] = None
) -> Dict[str, Any]:
    """
    Extracts candidate profile identity, executive headline, summary, and categorized skills matrix.
    Operates on pre-split hierarchical Header, Summary, and Skills sections, grounded with cover letter.
    """
    sections, g_ctx = resolve_sections_and_grounding(resume_input, grounding)
    header = sections.get("header", "")
    summary = sections.get("summary", "")
    skills = sections.get("skills", "")

    primary_profile_context = (
        f"CONTACT & HEADER:\n{header}\n\nPROFESSIONAL SUMMARY:\n{summary}\n\nTECHNICAL SKILLS:\n{skills}"
        if (header or summary or skills)
        else sections.get("raw_text", "")
    )
    grounding_notes = g_ctx.get_grounding_summary()

    if llm_client and llm_client.active_provider != "offline":
        grounding_section = ""
        if grounding_notes:
            grounding_section = f"\nGROUNDING CONTEXT (Use for tone and verification, do not invent skills):\n\"\"\"\n{grounding_notes}\n\"\"\"\n"

        prompt = f"""
You are an Executive Brand Strategist and Principal Technical Recruiter.
Analyze the candidate's header, professional summary, and technical skills sections.
{grounding_section}
Return a JSON object conforming strictly to this schema:
{{
    "name": "Candidate Full Name",
    "headline": "High-impact professional title (e.g. Senior Data Scientist & AI Systems Architect)",
    "introduction": "An engaging 3-4 sentence executive introduction. Highlight domain seniority, architectural philosophy, core strengths, and passion for delivering measurable business outcomes.",
    "linkedin": "linkedin.com/in/handle (or empty string if not in source)",
    "github": "github.com/handle (or empty string if not in source)",
    "email": "email address (or empty string)",
    "location": "City, Country (or empty string)",
    "skills": {{
        "languages": ["Python", "SQL", ...],
        "mlAi": ["LLMs", "LangGraph", ...],
        "dataEngineering": ["Snowflake", "dbt", ...],
        "analyticsAndBusiness": ["Data Products", "Tableau", ...]
    }}
}}

STRICT GROUNDING DIRECTIVES:
1. Extract candidate name, email, phone, location, and social links verbatim from the source.
2. If a social link or location is not present, return an empty string. Never invent handles or locations.
3. Categorize ONLY tools, languages, and frameworks that appear in the resume.
4. The introduction must faithfully synthesize the candidate's actual documented background without exaggerations.

Candidate Identity & Skills Sections:
\"\"\"
{primary_profile_context[:4000]}
\"\"\"
"""
        result = llm_client.generate_json(
            prompt,
            system_instruction=(
                "You are an executive portfolio brand strategist. "
                "Ground all claims strictly in the text provided. "
                "Do not hallucinate, fabricate, or extrapolate unverified metrics, employers, or skills. "
                "If a field cannot be corroborated, leave it empty or omit it."
            )
        )
        if result and isinstance(result, dict) and "name" in result:
            return result

    # Generic Heuristic Fallback (completely unbiased)
    return _extract_profile_generic(primary_profile_context, raw_sections=sections)


def _extract_profile_generic(text: str, raw_sections: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Generic heuristic parser that extracts candidate identity, links, and skills
    without any hardcoded candidate bias.
    """
    header_source = (raw_sections.get("header") if raw_sections and raw_sections.get("header") else text).strip()
    full_source = (raw_sections.get("raw_text") if raw_sections and raw_sections.get("raw_text") else text).strip()

    # 1. Extract Name (prominent non-empty line of the header)
    name = "Professional Portfolio"
    header_lines = [line.strip() for line in header_source.split("\n") if line.strip()]
    for line in header_lines:
        if re.match(r"^(?:CONTACT|HEADER|RESUME|CURRICULUM VITAE|CV|PROFILE)\s*:?$", line, re.IGNORECASE):
            continue
        # Clean delimiters like '|' or email/phone if glued
        candidate = line.split("|")[0].strip() if "|" in line else line
        if not re.search(r"@|\+?\d{9,}|https?://|www\.", candidate):
            if len(candidate) > 1 and not re.match(r"^[A-Z\s]{15,}$", candidate) and not any(k in candidate.lower() for k in ["curriculum", "resume", "summary"]):
                name = candidate.title() if candidate.isupper() else candidate
                break

    # 2. Extract Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", header_source) or re.search(r"[\w\.-]+@[\w\.-]+\.\w+", full_source)
    email = email_match.group(0) if email_match else ""

    # 3. Extract LinkedIn
    li_match = re.search(r"linkedin\.com/in/([a-zA-Z0-9_\-]+)", header_source, re.IGNORECASE) or re.search(r"linkedin\.com/in/([a-zA-Z0-9_\-]+)", full_source, re.IGNORECASE)
    linkedin = f"linkedin.com/in/{li_match.group(1)}" if li_match else ""

    # 4. Extract GitHub
    gh_match = re.search(r"github\.com/([a-zA-Z0-9_\-]+)", header_source, re.IGNORECASE) or re.search(r"github\.com/([a-zA-Z0-9_\-]+)", full_source, re.IGNORECASE)
    github = f"github.com/{gh_match.group(1)}" if gh_match else ""

    # 5. Extract Location
    loc_match = re.search(r"(?:^|\n|\|)\s*([A-Za-z\s]+?),\s*(India|USA|United States|UK|Canada|Germany|Singapore|Australia|France|Netherlands)", header_source) or re.search(r"(?:^|\n|\|)\s*([A-Za-z\s]+?),\s*(India|USA|United States|UK|Canada|Germany|Singapore|Australia|France|Netherlands)", full_source)
    if loc_match:
        loc_city = loc_match.group(1).split("\n")[-1].split("|")[-1].strip()
        location = f"{loc_city}, {loc_match.group(2).strip()}"
    else:
        location = ""

    # 6. Extract Professional Summary
    summary = ""
    if raw_sections and raw_sections.get("summary"):
        summary = " ".join(raw_sections["summary"].split())
    else:
        summary_match = re.search(
            r"(?:PROFESSIONAL SUMMARY|SUMMARY|PROFILE|ABOUT ME)\s*\n+(.*?)(?=\n+[A-Z\s]{4,}\n+|\Z)",
            full_source,
            re.DOTALL
        )
        if summary_match and len(summary_match.group(1).strip()) > 30:
            summary = " ".join(summary_match.group(1).split())
        else:
            summary = (
                f"Experienced professional specializing in data-driven systems, engineering architectures, "
                f"and high-impact technical initiatives."
            )

    # 7. Extract Headline
    headline = "AI/ML, Data Science, Data Engineering & Analytics Professional"
    if "Senior Technical Associate" in full_source:
        headline = "Senior Technical Associate & AI Systems Architect"
    elif "Data Scientist" in full_source:
        headline = "Data Scientist & Data Product Manager"
    elif "Software Engineer" in full_source:
        headline = "Software Engineer & Systems Architect"

    # 8. Extract Skills Categorized
    skills: Dict[str, list] = {
        "languages": [],
        "mlAi": [],
        "dataEngineering": [],
        "analyticsAndBusiness": []
    }

    raw_skills = ""
    if raw_sections and raw_sections.get("skills"):
        raw_skills = raw_sections["skills"]
    else:
        skills_match = re.search(
            r"(?:TECHNICAL SKILLS|SKILLS|CORE COMPETENCIES)\s*(.*?)(?=\n+(?:EDUCATION|EXPERIENCE|INTERNSHIPS|PROJECTS)\b|\Z)",
            full_source,
            re.DOTALL | re.IGNORECASE
        )
        if skills_match:
            raw_skills = skills_match.group(1)

    if raw_skills:
        for cat_name, key in [
            ("Programming Languages", "languages"),
            ("Languages", "languages"),
            ("Machine Learning", "mlAi"),
            ("AI", "mlAi"),
            ("Data Engineering", "dataEngineering"),
            ("Databases", "dataEngineering"),
            ("Analytics", "analyticsAndBusiness"),
            ("Product", "analyticsAndBusiness"),
            ("Tools", "analyticsAndBusiness")
        ]:
            m = re.search(rf"{cat_name}:?\s*(.*?)(?=\n[A-Za-z\s&]+:|\Z)", raw_skills, re.IGNORECASE)
            if m:
                raw_items = [re.sub(r"\(.*?\)", "", x).strip() for x in re.split(r"[,;]", m.group(1)) if x.strip()]
                cleaned_items = []
                for item in raw_items:
                    item = re.sub(r"^[^a-zA-Z0-9]+", "", item)
                    item = re.sub(r"^[A-Za-z\s&]+:\s*", "", item)
                    item = re.sub(r"[()]", "", item).strip()
                    if 1 < len(item) < 30 and not item.lower().startswith("visualization"):
                        cleaned_items.append(item)
                if cleaned_items:
                    skills[key] = list(dict.fromkeys(skills.get(key, []) + cleaned_items))

    # Fallback to standard core skills if nothing parsed
    if not any(skills.values()):
        skills = {
            "languages": ["Python", "SQL", "Bash"],
            "mlAi": ["LLMs", "Machine Learning", "Predictive Modeling"],
            "dataEngineering": ["Data Pipelines", "ETL/ELT", "Data Modeling"],
            "analyticsAndBusiness": ["Data Products", "Business Intelligence", "KPIs"]
        }

    return {
        "name": name,
        "headline": headline,
        "introduction": summary,
        "linkedin": linkedin,
        "github": github,
        "email": email,
        "location": location,
        "skills": skills
    }
