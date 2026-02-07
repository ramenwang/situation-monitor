"""
Utility helper functions.
"""

import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from html import unescape


def hash_code(s: str) -> str:
    """Generate a stable hash from a string."""
    return hashlib.md5(s.encode()).hexdigest()[:12]


def generate_id(url: str, source: str) -> str:
    """Generate a unique ID from URL and source."""
    url_hash = hash_code(url)
    source_hash = hash_code(source)
    return f"{source_hash}-{url_hash}"


def parse_gdelt_date(date_str: str) -> str:
    """
    Parse GDELT date format (20251202T224500Z) to ISO8601.
    """
    if not date_str:
        return datetime.utcnow().isoformat() + "Z"

    # Try GDELT format: 20251202T224500Z
    match = re.match(r'^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$', date_str)
    if match:
        year, month, day, hour, minute, sec = match.groups()
        return f"{year}-{month}-{day}T{hour}:{minute}:{sec}Z"

    # Try standard parsing
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.isoformat().replace('+00:00', 'Z')
    except ValueError:
        return datetime.utcnow().isoformat() + "Z"


def parse_rss_date(date_str: str) -> str:
    """
    Parse various RSS date formats to ISO8601.
    """
    if not date_str:
        return datetime.utcnow().isoformat() + "Z"

    # Common RSS date formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 2822
        "%a, %d %b %Y %H:%M:%S %Z",       # RFC 2822 with timezone name
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",             # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",              # Simple datetime
        "%Y-%m-%d",                        # Date only
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat().replace('+00:00', 'Z')
        except ValueError:
            continue

    # Fallback
    return datetime.utcnow().isoformat() + "Z"


def now_iso() -> str:
    """Get current ISO8601 timestamp."""
    return datetime.utcnow().isoformat() + "Z"


def strip_html(html: str) -> str:
    """
    Remove HTML tags and decode entities.
    """
    if not html:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)

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


def truncate(text: str, max_length: int = 300) -> str:
    """
    Truncate text to max length, preferring sentence boundaries.
    """
    if not text or len(text) <= max_length:
        return text

    truncated = text[:max_length]

    # Try to break at sentence boundary
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclaim = truncated.rfind('!')

    boundary = max(last_period, last_question, last_exclaim)

    if boundary > max_length * 0.5:
        return text[:boundary + 1]

    # Fall back to word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:
        return text[:last_space] + "..."

    return truncated + "..."


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""
