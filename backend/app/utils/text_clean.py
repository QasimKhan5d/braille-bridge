"""Utility functions for preparing Urdu text before Braille conversion."""
import re

# Regex that matches ASCII letters, digits and common punctuation which we want to drop
# Added backslash to the character class, but keep Urdu question mark ؟
_DROP_PUNCT = re.compile(r"[A-Za-z0-9_\\\-~`!@#$%^&*()\[\]{};:\"',.<>/|]+")

def clean_source(text: str) -> str:
    """Return *text* with ASCII / punctuation removed and whitespace normalised.

    This prevents liblouis from outputting 8-dot Braille patterns for
    characters that are outside the Urdu alphabet (e.g. '-' ↦ ⡳).
    """
    # Replace ASCII question mark with Urdu question mark
    text = text.replace('?', '؟')
    
    # Remove unwanted characters
    text = _DROP_PUNCT.sub(" ", text)
    # Collapse consecutive whitespace to a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()
