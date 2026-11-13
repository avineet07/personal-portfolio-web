"""
section_splitter.py — Hierarchical resume section identification & grounding context.

Identifies the hierarchical boundaries and structural splits in a generic CV
(Header, Professional Summary, Technical Skills, Experience, Education, Internships, Projects),
isolating each section for focused extraction while maintaining grounding references
from the cover letter and verified content articles.
"""

import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field


# Canonical Section Matching Patterns (ordered for boundary detection)
SECTION_PATTERNS = [
    ("summary", r"(?:^|\n)\s*(?:PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY|SUMMARY|PROFILE|ABOUT ME)\s*(?:\n|$)"),
    ("experience", r"(?:^|\n)\s*(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY|CAREER HISTORY)\s*(?:\n|$)"),
    ("education", r"(?:^|\n)\s*(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC CREDENTIALS|QUALIFICATIONS)\s*(?:\n|$)"),
    ("skills", r"(?:^|\n)\s*(?:TECHNICAL SKILLS|SKILLS & EXPERTISE|SKILLS|CORE COMPETENCIES|AREAS OF EXPERTISE)\s*(?:\n|$)"),
    ("internships", r"(?:^|\n)\s*(?:INTERNSHIPS|INTERNSHIP EXPERIENCE|EARLY CAREER)\s*(?:\n|$)"),
    ("projects", r"(?:^|\n)\s*(?:PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|ACADEMIC PROJECTS|PUBLICATIONS)\s*(?:\n|$)"),
    ("certifications", r"(?:^|\n)\s*(?:CERTIFICATIONS|LICENSES & CERTIFICATIONS|AWARDS & HONORS|HONORS)\s*(?:\n|$)"),
]


def split_resume_into_sections(resume_text: str) -> Dict[str, str]:
    """
    Parses a resume text into structured, hierarchical section slices.
    Returns a dictionary of section names mapped to their respective text content.
    """
    if not resume_text:
        return {
            "header": "",
            "summary": "",
            "skills": "",
            "experience": "",
            "education": "",
            "internships": "",
            "projects": "",
            "certifications": "",
            "raw_text": "",
        }

    # Find all section headers and their character coordinates
    matches = []
    for sec_name, pattern in SECTION_PATTERNS:
        for m in re.finditer(pattern, resume_text, re.IGNORECASE):
            matches.append((m.start(), m.end(), sec_name, m.group(0).strip()))

    # Sort matches chronologically by appearance in the document
    matches.sort(key=lambda x: x[0])

    sections: Dict[str, str] = {
        "header": "",
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "internships": "",
        "projects": "",
        "certifications": "",
        "raw_text": resume_text,
    }

    # Header is everything prior to the very first section heading
    if matches:
        sections["header"] = resume_text[:matches[0][0]].strip()
    else:
        sections["header"] = resume_text.strip()

    # Slice each identified section
    for i, m in enumerate(matches):
        sec_name = m[2]
        start = m[1]
        end = matches[i + 1][0] if i + 1 < len(matches) else len(resume_text)
        chunk = resume_text[start:end].strip()

        # If clean chunk is not empty, append or assign
        if chunk:
            if sections[sec_name]:
                sections[sec_name] += "\n\n" + chunk
            else:
                sections[sec_name] = chunk

    # Secondary Heuristic: If internships were not explicitly partitioned
    # check if internships were embedded in the experience section
    if not sections["internships"] and sections["experience"]:
        intern_split = re.search(
            r"(?:^|\n)\s*(?:INTERNSHIPS|INTERNSHIP EXPERIENCE)\s*(?:\n|$)",
            sections["experience"],
            re.IGNORECASE
        )
        if intern_split:
            exp_part = sections["experience"][:intern_split.start()].strip()
            intern_part = sections["experience"][intern_split.end():].strip()
            sections["experience"] = exp_part
            sections["internships"] = intern_part

    return sections


@dataclass
class GroundingContext:
    """
    Encapsulates secondary resources (cover letter, published case studies)
    used strictly for grounding, corroboration, and alignment.
    """
    cover_letter: str = ""
    source_documents: Dict[str, Optional[str]] = field(default_factory=dict)
    content_articles: List[Dict[str, Any]] = field(default_factory=list)

    def get_grounding_summary(self) -> str:
        """Returns a concise grounding brief to augment generator prompts."""
        parts = []
        if self.cover_letter:
            clean_cl = " ".join(self.cover_letter.split())
            if len(clean_cl) > 1200:
                clean_cl = clean_cl[:1200] + "..."
            parts.append(f"COVER LETTER NARRATIVE (Use for alignment):\n{clean_cl}")

        if self.content_articles:
            art_titles = [f"- {a.get('title')} ({a.get('topic', 'Engineering')})" for a in self.content_articles[:4]]
            parts.append("VERIFIED CONTENT PORTFOLIO ARTICLES:\n" + "\n".join(art_titles))

        return "\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_cover_letter": bool(self.cover_letter),
            "cover_letter_length": len(self.cover_letter),
            "source_documents": self.source_documents,
            "article_count": len(self.content_articles)
        }


def resolve_sections_and_grounding(
    input_data: Union[str, Dict[str, str]],
    grounding: Optional[Union[GroundingContext, Dict[str, Any], str]] = None
) -> tuple[Dict[str, str], GroundingContext]:
    """
    Helper utility for generators to gracefully handle either raw text strings
    or pre-split section dictionaries, along with optional grounding context.
    """
    if isinstance(input_data, dict) and "raw_text" in input_data:
        sections = input_data
    elif isinstance(input_data, dict):
        sections = input_data
        sections.setdefault("raw_text", "\n\n".join(str(v) for v in input_data.values()))
    else:
        sections = split_resume_into_sections(str(input_data))

    if isinstance(grounding, GroundingContext):
        g_ctx = grounding
    elif isinstance(grounding, dict):
        g_ctx = GroundingContext(
            cover_letter=grounding.get("cover_letter", ""),
            source_documents=grounding.get("source_documents", {}),
            content_articles=grounding.get("content_articles", [])
        )
    elif isinstance(grounding, str):
        g_ctx = GroundingContext(cover_letter=grounding)
    else:
        g_ctx = GroundingContext()

    return sections, g_ctx

