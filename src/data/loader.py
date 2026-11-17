"""
loader.py — Generic data loader for portfolio structured content.

Loads the active portfolio dataset from src/data/portfolio_data.json.
If portfolio_data.json is not present, falls back cleanly to the static baseline
archive in src/data/portfolio_data_historical.json with zero hardcoded biases.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple

DATA_DIR = Path(__file__).resolve().parent
PORTFOLIO_JSON = DATA_DIR / "portfolio_data.json"
HISTORICAL_JSON = DATA_DIR / "portfolio_data_historical.json"


def get_fallback_portfolio() -> Dict[str, Any]:
    """
    Loads fallback portfolio data from portfolio_data_historical.json if present,
    otherwise returns a clean, generic structural template.
    """
    if HISTORICAL_JSON.is_file():
        try:
            with open(HISTORICAL_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading {HISTORICAL_JSON}: {e}")

    # Completely generic structural baseline without personal bias
    return {
        "version": "1.0",
        "profile": {
            "name": "Professional Portfolio",
            "headline": "Engineering & Technology Professional",
            "introduction": "Welcome to my portfolio website showcasing my technical projects, engineering work, and experience.",
            "linkedin": "",
            "github": "",
            "email": "",
            "location": "",
            "skills": {
                "languages": [],
                "mlAi": [],
                "dataEngineering": [],
                "analyticsAndBusiness": []
            }
        },
        "resume": {
            "introduction": "Welcome to my portfolio website showcasing my technical projects, engineering work, and experience.",
            "headline": "Engineering & Technology Professional",
            "pillars": [],
            "workExperience": [],
            "internships": [],
            "education": [],
            "title": "Professional Portfolio & Case Studies",
            "meta_description": "Portfolio and engineering case studies."
        },
        "content_meta": {
            "matched_work_count": 0,
            "scaffolded_cases": []
        }
    }


def load_portfolio_json() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns (profile_data, resume_data) loaded from portfolio_data.json.
    Supports simplified flat schemas, clean grouped schemas, and legacy nested schemas.
    Falls back to portfolio_data_historical.json if portfolio_data.json is missing or corrupted.
    """
    # 1. Try loading user-generated / active portfolio_data.json
    if PORTFOLIO_JSON.is_file():
        try:
            with open(PORTFOLIO_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                # Resolve profile fields
                if "profile" in data and isinstance(data["profile"], dict):
                    profile = dict(data["profile"])
                else:
                    profile = {
                        "name": data.get("name", ""),
                        "headline": data.get("headline", ""),
                        "introduction": data.get("introduction", ""),
                        "linkedin": data.get("linkedin", ""),
                        "github": data.get("github", ""),
                        "email": data.get("email", ""),
                        "location": data.get("location", ""),
                        "skills": data.get("skills", {}),
                        "resume_url": data.get("resume_url", "/assets/resume.pdf")
                    }
                profile["resume_url"] = profile.get("resume_url") or data.get("resume_url", "/assets/resume.pdf")

                # Resolve resume fields
                if "resume" in data and isinstance(data["resume"], dict):
                    resume = dict(data["resume"])
                else:
                    resume = {}

                # Fill career and narrative lists from root if not in resume
                if "pillars" not in resume:
                    resume["pillars"] = data.get("pillars", [])
                if "workExperience" not in resume:
                    resume["workExperience"] = data.get("workExperience", data.get("experience", []))
                if "education" not in resume:
                    resume["education"] = data.get("education", [])
                if "internships" not in resume:
                    resume["internships"] = data.get("internships", [])
                if "title" not in resume:
                    candidate_name = profile.get("name") or data.get("name", "Engineering Professional")
                    resume["title"] = data.get("title", f"{candidate_name} | Portfolio & Case Studies")
                if "meta_description" not in resume:
                    resume["meta_description"] = data.get("meta_description", "")

                # Synchronize single source of truth for introduction & headline
                intro = profile.get("introduction") or resume.get("introduction") or data.get("introduction", "")
                headline = profile.get("headline") or resume.get("headline") or data.get("headline", "")

                profile["introduction"] = intro
                resume["introduction"] = intro
                profile["headline"] = headline
                resume["headline"] = headline

                if profile.get("name") or resume.get("workExperience"):
                    return profile, resume
        except Exception as e:
            print(f"⚠️ Failed to parse {PORTFOLIO_JSON}: {e}. Falling back to historical dataset.")

    # 2. Fall back to historical baseline JSON
    fallback = get_fallback_portfolio()
    return fallback["profile"], fallback["resume"]
