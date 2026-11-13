"""
data package — Portfolio structured data, static compilation, and loaders.
"""

from .loader import load_portfolio_json, get_fallback_portfolio

__all__ = ["load_portfolio_json", "get_fallback_portfolio"]

