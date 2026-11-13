"""
pillars_generator.py — Generic, insightful synthesis of core technical & architectural pillars.

Synthesizes 3-4 architectural domain pillars reflecting the candidate's primary
technical depth, system design capabilities, and engineering philosophies.
"""

import re
from typing import List, Dict, Any, Optional, Union
from ..llm_client import LLMClient
from ..section_splitter import resolve_sections_and_grounding, GroundingContext


def generate_pillars(
    resume_input: Union[str, Dict[str, str]],
    llm_client: Optional[LLMClient] = None,
    grounding: Optional[Union[GroundingContext, Dict[str, Any], str]] = None
) -> List[Dict[str, Any]]:
    """
    Synthesizes 3-4 core architectural pillars representing the candidate's technical mastery.
    Operates on hierarchical resume sections grounded by verified secondary materials.
    """
    sections, g_ctx = resolve_sections_and_grounding(resume_input, grounding)
    core_context = f"""
TECHNICAL SKILLS:
{sections.get('skills', '')}

WORK EXPERIENCE:
{sections.get('experience', '')}

SUMMARY & ACHIEVEMENTS:
{sections.get('summary', '')}
""".strip()

    if llm_client and llm_client.active_provider != "offline":
        grounding_block = ""
        grounding_summary = g_ctx.get_grounding_summary()
        if grounding_summary:
            grounding_block = f"\nVERIFIED GROUNDING CONTEXT:\n{grounding_summary}\n"

        prompt = f"""
You are a Principal Technical Fellow and Executive Engineering Architect.
Examine the candidate's career experience and technical achievements in the provided text.
Synthesize 3-4 authoritative "Core Technical Pillars" that capture the candidate's
deepest architectural disciplines and strategic value proposition.

Each pillar must represent a distinct technical domain (e.g., Agentic AI & Systems, Distributed Data Platforms, Predictive ML & Retention, Real-Time Streaming & CDC).

Return a JSON array of 3-4 objects with this exact structure:
[
  {{
    "tag": "UPPERCASE DOMAIN CATEGORY (e.g. AGENTIC AI & LLMS, DATA PLATFORM ARCHITECTURE)",
    "title": "Authoritative Architecture Headline (e.g. Production Agentic AI Workflows)",
    "description": [
      "Concrete technical point detailing stateful design, frameworks, and architecture...",
      "Governance, evaluation, error handling, or latency optimization detail...",
      "Measurable business impact, cost efficiency, or stakeholder enablement..."
    ]
  }}
]

GROUNDING RULES:
- Pillars MUST be derived strictly from technical areas the candidate actually worked on in the text.
- Do not invent architectures, platforms, or tools not present in the candidate's history.
- Each pillar's description must contain 2 to 3 substantive, professional sentences.
{grounding_block}
Candidate Resume / Profile Context:
\"\"\"
{core_context[:4000] or sections.get('raw_text', '')[:4000]}
\"\"\"
"""
        result = llm_client.generate_json(
            prompt,
            system_instruction=(
                "You are an executive engineering fellow. "
                "Synthesize architectural pillars strictly from verified systems, architectures, and tools in the resume text. "
                "Never invent fictional technologies, architectures, or statistics."
            )
        )
        if result and isinstance(result, list) and len(result) >= 3:
            return result[:4]
        if result and isinstance(result, dict) and "pillars" in result:
            return result["pillars"][:4]

    # Generic Heuristic Fallback
    return _generate_pillars_generic(sections.get("raw_text", ""))


def _generate_pillars_generic(text: str) -> List[Dict[str, Any]]:
    """
    Synthesizes architectural pillars dynamically by analyzing the technical domains
    present in the candidate's actual resume text.
    """
    lower_text = text.lower()
    pillars: List[Dict[str, Any]] = []

    # Domain 1: Agentic AI / LLMs
    if any(k in lower_text for k in ["langgraph", "agent", "llm", "prompt", "openai", "hallucination", "rag"]):
        pillars.append({
            "tag": "AI/ML & AGENTIC SYSTEMS",
            "title": "Agentic AI & LLM Systems in Production",
            "description": [
                "Architected cyclic state graphs with conditional routing and Human-in-the-Loop (HITL) checkpoints.",
                "Engineered automated evaluation pipelines for workflow adherence, sentiment drift, and hallucination detection.",
                "Integrated production LLM solutions boosting task completion rates and operational efficiency."
            ]
        })

    # Domain 2: Data Mesh / Architecture
    if any(k in lower_text for k in ["data mesh", "data product", "dbt", "governance", "schema", "superset", "mart"]):
        pillars.append({
            "tag": "DATA-DRIVEN DECISION ARCHITECTURE",
            "title": "Enterprise Data Mesh & Data Products",
            "description": [
                "Implemented domain-oriented decentralized data ownership across business functions.",
                "Constructed standardized data marts and automated rule engines for self-serve analytics.",
                "Delivered end-to-end data products combining ETL, low-latency APIs, and executive metric layers."
            ]
        })

    # Domain 3: Machine Learning / Modeling
    if any(k in lower_text for k in ["lightgbm", "classifier", "churn", "predictive", "propensity", "a/b test", "logistic regression"]):
        pillars.append({
            "tag": "MACHINE LEARNING",
            "title": "Predictive ML & Customer Retention",
            "description": [
                "Engineered high-volume transaction features and gradient-boosted tree classifiers for customer behavior modeling.",
                "Designed targeted ML campaigns with causal inference and Design of Experiments (DoE) methodologies.",
                "Translated algorithmic predictions into automated downstream triggers improving portfolio retention."
            ]
        })

    # Domain 4: Data Engineering / CDC / Streaming
    if any(k in lower_text for k in ["snowflake", "snowpipe", "cdc", "dms", "airflow", "warehouse", "s3", "spark"]):
        pillars.append({
            "tag": "DATA PLATFORM ENGINEERING",
            "title": "Data Pipelines & Warehousing Infrastructure",
            "description": [
                "Implemented event-driven Change Data Capture (CDC) streaming into cloud data warehouses.",
                "Streamlined data pipelines utilizing micro-batch stages, auto-ingestion pipes, and stream tasks.",
                "Optimized SQL query performance and data modeling to deliver substantial compute cost savings."
            ]
        })

    # Generic Fallbacks if candidate worked in different domains (e.g. general software or backend)
    if len(pillars) < 3:
        if any(k in lower_text for k in ["cloud", "docker", "kubernetes", "aws", "gcp", "azure"]):
            pillars.append({
                "tag": "CLOUD & PLATFORM INFRASTRUCTURE",
                "title": "Scalable Cloud Architecture & DevOps",
                "description": [
                    "Engineered cloud infrastructure with high availability, microservices, and containerization.",
                    "Configured CI/CD automation pipelines for reliable and rapid production deployments.",
                    "Optimized cloud resource allocation, monitoring, and infrastructure security."
                ]
            })

    if len(pillars) < 3:
        pillars.append({
            "tag": "TECHNICAL LEADERSHIP",
            "title": "Full-Lifecycle System Engineering",
            "description": [
                "Led end-to-end delivery of complex technical platforms from conceptual proof-of-concept to production.",
                "Collaborated with cross-functional product and engineering stakeholders to solve high-stakes challenges.",
                "Maintained rigorous standards for code quality, documentation, testing, and system reliability."
            ]
        })

    return pillars[:4]
