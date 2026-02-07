"""
Text parsing utilities.
"""

import re
from html import unescape
from typing import Optional


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    - Removes HTML tags
    - Decodes HTML entities
    - Normalizes whitespace
    - Removes common RSS artifacts
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Decode HTML entities
    text = unescape(text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common RSS artifacts
    text = re.sub(r'\[…\]', '...', text)
    text = re.sub(r'\[\.\.\.\]', '...', text)
    text = re.sub(r'Continue reading\.\.\.?$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Read more\.\.\.?$', '', text, flags=re.IGNORECASE)

    return text.strip()


def extract_summary(content: str, max_length: int = 300) -> str:
    """
    Extract summary from content.

    Truncates at sentence boundary if possible.
    """
    if not content:
        return ""

    clean = clean_text(content)

    if len(clean) <= max_length:
        return clean

    # Try to break at sentence boundary
    truncated = clean[:max_length]

    # Find last sentence ending
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclaim = truncated.rfind('!')

    boundary = max(last_period, last_question, last_exclaim)

    if boundary > max_length * 0.5:
        return clean[:boundary + 1]

    # Fall back to word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:
        return clean[:last_space] + "..."

    return truncated + "..."


class TextParser:
    """
    Text parsing utilities.

    Example usage:
        parser = TextParser()
        clean = parser.clean(html_text)
        summary = parser.extract_summary(long_text, max_length=200)
        sentences = parser.split_sentences(text)
    """

    def clean(self, text: str) -> str:
        """Clean and normalize text."""
        return clean_text(text)

    def extract_summary(self, content: str, max_length: int = 300) -> str:
        """Extract summary from content."""
        return extract_summary(content, max_length)

    def split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Simple implementation - for production consider using NLTK or spaCy.
        """
        if not text:
            return []

        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_quotes(self, text: str) -> list[str]:
        """Extract quoted text."""
        if not text:
            return []

        # Match various quote styles
        patterns = [
            r'"([^"]+)"',       # Double quotes
            r"'([^']+)'",       # Single quotes
            r'"([^"]+)"',       # Smart quotes
            r'«([^»]+)»',       # Guillemets
        ]

        quotes = []
        for pattern in patterns:
            quotes.extend(re.findall(pattern, text))

        return quotes

    def extract_numbers(self, text: str) -> list[str]:
        """Extract numbers (including percentages, currencies)."""
        if not text:
            return []

        # Match various number formats
        pattern = r'[-+]?\$?\d+(?:,\d{3})*(?:\.\d+)?%?'
        return re.findall(pattern, text)

    def word_count(self, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())
