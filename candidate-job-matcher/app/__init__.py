"""
Candidate-Job Matcher Application
Main application package initialization
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "LLM-Powered Candidate-Job Matching System"

from app.config import settings, get_settings

__all__ = [
    "settings",
    "get_settings",
]