"""
profile.py — Global identity for the portfolio.

Loads identity dynamically from the compiled static JSON (src/data/portfolio_data.json)
if available, or uses static defaults from data.loader.
"""

import os
import sys

# Support direct and relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from data.loader import load_portfolio_json
    _profile, _ = load_portfolio_json()
    profile_data = _profile
except Exception:
    from data.loader import get_fallback_portfolio
    profile_data = get_fallback_portfolio()["profile"]
