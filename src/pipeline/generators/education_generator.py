"""
education_generator.py — Generic, unbiased extraction of education and internships.

Extracts academic credentials and early career internships from any resume.
Contains zero hardcoded universities, institutions, or company names.
"""

import re
from typing import Dict, Any, List, Optional, Union
from ..llm_client import LLMClient
from ..section_splitter import resolve_sections_and_grounding, GroundingContext


def generate_education_and_internships(
    resume_input: Union[str, Dict[str, str]],
    llm_client: Optional[LLMClient] = None,
    grounding: Optional[Union[GroundingContext, Dict[str, Any], str]] = None
) -> Dict[str, Any]:
    """
    Extracts education qualifications and internships from the resume without bias.
    Operates on pre-split hierarchical Education and Internships sections.
    """
    sections, g_ctx = resolve_sections_and_grounding(resume_input, grounding)
    edu_text = sections.get("education", "")
    intern_text = sections.get("internships", "")
    combined_academic = (
        f"EDUCATION:\n{edu_text}\n\nINTERNSHIPS:\n{intern_text}"
        if (edu_text or intern_text)
        else sections.get("raw_text", "")
    )
    grounding_notes = g_ctx.get_grounding_summary()

    if llm_client and llm_client.active_provider != "offline":
        grounding_section = ""
        if grounding_notes:
            grounding_section = f"\nGROUNDING CONTEXT (Use for alignment, do not invent degrees):\n\"\"\"\n{grounding_notes}\n\"\"\"\n"

        prompt = f"""
You are an Academic Credential & Career Verification Specialist.
Extract all higher education degrees, universities, graduation periods, fields of study,
and early-career internships from the provided resume sections.
{grounding_section}
Return a JSON object with this exact structure:
{{
  "education": [
    {{
      "degree": "Degree Title (e.g. B.Tech + M.Tech / Bachelor of Science)",
      "institution": "Full University or Institution Name",
      "period": "Start Year – End Year (e.g. 2014 – 2019)",
      "field": "Major / Field of Study (e.g. Materials Engineering / Computer Science)"
    }}
  ],
  "internships": [
    {{
      "role": "Role / Internship Title",
      "company": "Company Name",
      "location": "City, Country (or empty string)",
      "period": "Period (e.g. May 2018 – Jul 2018)",
      "description": "High-signal description of key technical deliverables during the internship."
    }}
  ]
}}

GROUNDING RULES:
- Only extract institutions and degrees that are explicitly stated in the text.
- If no internships are listed, return an empty array for "internships".
- Do not invent GPA, honors, or credentials not in the source text.

Resume Academic & Internship Sections:
\"\"\"
{combined_academic}
\"\"\"
"""
        result = llm_client.generate_json(
            prompt,
            system_instruction=(
                "You are an academic credential verification parser. "
                "Only extract degrees, universities, fields, and internships explicitly stated in the source text. "
                "Never invent qualifications or employers."
            )
        )
        if result and isinstance(result, dict) and "education" in result:
            return result

    # Generic Heuristic Fallback
    return _extract_education_generic(combined_academic, raw_sections=sections)


def _extract_education_generic(text: str, raw_sections: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Generic heuristic parser that extracts university degrees and internships
    based on standard structural resume patterns without any institution hardcoding.
    """
    education: List[Dict[str, Any]] = []
    internships: List[Dict[str, Any]] = []

    # 1. Parse Education Section
    edu_match = re.search(
        r"(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS)\s*\n+(.*?)(?=\n+(?:TECHNICAL SKILLS|SKILLS|INTERNSHIPS|PROJECTS|EXPERIENCE|PUBLICATIONS)\b|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if edu_match:
        edu_text = edu_match.group(1).strip()
    elif raw_sections and raw_sections.get("education"):
        edu_text = raw_sections["education"].strip()
    else:
        edu_text = text.strip()

    if edu_text:
        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]

        # Common degree keywords to identify degree lines
        degree_pattern = r"(?:B\.?Tech|M\.?Tech|Dual Degree|B\.?S\.?|M\.?S\.?|Ph\.?D|Bachelor|Master|Diploma|Associate)"
        date_pattern = r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}\s*[\u2013\u2014\-–]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}"

        i = 0
        while i < len(lines):
            line = lines[i]
            # Check if this line or next has institution or degree
            institution = line
            period = ""
            date_m = re.search(date_pattern, line)
            if date_m:
                period = date_m.group(0).strip()
                institution = line[:date_m.start()].strip()

            degree = "Degree"
            field = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.search(degree_pattern, next_line, re.IGNORECASE) or len(next_line) < 60:
                    degree = next_line
                    i += 1

            if i + 1 < len(lines):
                third_line = lines[i + 1]
                # If third line isn't a new date, digit (page number), or section, it's likely the field of study
                if not re.search(date_pattern, third_line) and not third_line.isdigit() and len(third_line) < 80 and not third_line.startswith(("•", "-")):
                    field = third_line
                    i += 1

            if field.isdigit() or len(field) <= 2:
                field = ""

            if institution:
                # Clean up PDF font-spacing kerning artifacts (e.g. 'T echnology' -> 'Technology')
                institution = re.sub(r"\bT\s+echnology\b", "Technology", institution)
                institution = re.sub(r"\s+,\s*", ", ", institution).strip()
                # Filter out pure numbers from institution
                if not institution.isdigit():
                    education.append({
                        "degree": degree,
                        "institution": institution,
                        "period": period,
                        "field": field
                    })
            i += 1

    # 2. Parse Internships Section
    intern_match = re.search(
        r"(?:INTERNSHIPS|EARLY CAREER|INTERNSHIP EXPERIENCE)\s*\n+(.*?)(?=\n+(?:TECHNICAL SKILLS|SKILLS|EDUCATION|PROJECTS|PUBLICATIONS)\b|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if intern_match:
        intern_text = intern_match.group(1).strip()
    elif raw_sections and raw_sections.get("internships"):
        intern_text = raw_sections["internships"].strip()
    else:
        intern_text = ""

    if intern_text:
        intern_lines = [l.strip() for l in intern_text.split("\n") if l.strip()]

        date_pattern = r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}\s*[\u2013\u2014\-–]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}"

        i = 0
        while i < len(intern_lines):
            line = intern_lines[i]
            date_m = re.search(date_pattern, line)
            role = "Intern"
            period = ""
            if date_m:
                period = date_m.group(0).strip()
                role_part = line[:date_m.start()].strip()
                role = role_part if role_part else "Intern"
            else:
                role = line

            company = "Company"
            location = ""
            desc = ""

            if i + 1 < len(intern_lines):
                comp_loc = intern_lines[i + 1]
                parts = [p.strip() for p in comp_loc.split(",") if p.strip()]
                company = parts[0] if parts else "Company"
                location = ", ".join(parts[1:]) if len(parts) > 1 else ""
                i += 1

            # Check for description
            if i + 1 < len(intern_lines) and not re.search(date_pattern, intern_lines[i + 1]):
                candidate_desc = intern_lines[i + 1]
                if not candidate_desc.isdigit() and len(candidate_desc) > 5:
                    desc = candidate_desc
                    i += 1
                else:
                    desc = f"Formative engineering and data analytics projects completed at {company}."
            else:
                desc = f"Formative engineering and data analytics projects completed at {company}."

            if not role.isdigit() and len(role) > 2 and company != "Company":
                internships.append({
                    "role": role,
                    "company": company,
                    "location": location,
                    "period": period,
                    "description": desc
                })
            i += 1

    return {
        "education": education,
        "internships": internships
    }
