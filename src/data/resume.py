"""
resume.py — Home page career narrative.

Loads narrative dynamically from the compiled static JSON (src/data/portfolio_data.json)
if available, or uses static defaults from data.loader.
"""

import os
import sys

# Support direct and relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from data.loader import load_portfolio_json
    _, resume_data = load_portfolio_json()
except Exception:
    from data.loader import get_fallback_portfolio
    resume_data = get_fallback_portfolio()["resume"]

introduction = resume_data.get("introduction", "")
pillars = resume_data.get("pillars", [])
workExperience = resume_data.get("workExperience", [])
internships = resume_data.get("internships", [])
education = resume_data.get("education", [])
title = resume_data.get("title","")
meta_description = resume_data.get("meta_description", "")
