"""
Topic Detection

Detects topics from news text using keyword matching.
Extensible - can add ML-based detection later.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class TopicConfig:
    """Configuration for a topic."""
    name: str
    keywords: list[str]
    weight: float = 1.0  # For scoring/ranking


# Default topic configurations
DEFAULT_TOPICS: dict[str, list[str]] = {
    "FINANCE": [
        "fed", "federal reserve", "interest rate", "inflation", "gdp",
        "unemployment", "recession", "rally", "crash", "stock", "market",
        "earnings", "quarterly", "dividend", "ipo", "merger", "acquisition",
    ],
    "CRYPTO": [
        "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
        "blockchain", "defi", "nft", "stablecoin", "binance", "coinbase",
    ],
    "TECH": [
        "ai", "artificial intelligence", "machine learning", "startup",
        "ipo", "acquisition", "layoff", "tech company", "silicon valley",
        "software", "saas", "cloud computing",
    ],
    "CYBER": [
        "cyber", "hack", "hacker", "ransomware", "malware", "breach",
        "vulnerability", "exploit", "phishing", "apt", "zero-day",
    ],
    "CONFLICT": [
        "war", "military", "troops", "invasion", "strike", "missile",
        "combat", "offensive", "ceasefire", "casualties", "bombing",
    ],
    "NUCLEAR": [
        "nuclear", "icbm", "warhead", "nonproliferation", "uranium",
        "plutonium", "reactor", "enrichment",
    ],
    "ENERGY": [
        "oil", "crude", "opec", "natural gas", "lng", "energy",
        "petroleum", "pipeline", "refinery",
    ],
    "GEOPOLITICS": [
        "sanctions", "tariff", "trade war", "diplomatic", "embassy",
        "treaty", "summit", "bilateral", "nato", "g7", "g20",
    ],
}


class TopicDetector:
    """
    Detects topics in text using keyword matching.

    Example usage:
        detector = TopicDetector()
        topics = detector.detect("Federal Reserve raises interest rates")
        # Returns: ["FINANCE"]

        # With custom topics:
        detector = TopicDetector(topics={"CUSTOM": ["keyword1", "keyword2"]})

        # Add topics at runtime:
        detector.add_topic("BIOTECH", ["gene", "therapy", "pharmaceutical"])
    """

    def __init__(
        self,
        topics: Optional[dict[str, list[str]]] = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize topic detector.

        Args:
            topics: Custom topic definitions. If None, uses DEFAULT_TOPICS.
            case_sensitive: Whether to match case-sensitively.
        """
        self.topics = topics if topics is not None else DEFAULT_TOPICS.copy()
        self.case_sensitive = case_sensitive

    def detect(self, text: str) -> list[str]:
        """
        Detect topics in text.

        Args:
            text: Text to analyze.

        Returns:
            List of detected topic names.
        """
        if not text:
            return []

        search_text = text if self.case_sensitive else text.lower()
        detected = []

        for topic, keywords in self.topics.items():
            for keyword in keywords:
                kw = keyword if self.case_sensitive else keyword.lower()
                if kw in search_text:
                    detected.append(topic)
                    break  # One match per topic is enough

        return detected

    def detect_with_scores(self, text: str) -> dict[str, int]:
        """
        Detect topics with match counts.

        Args:
            text: Text to analyze.

        Returns:
            Dict of topic -> match count.
        """
        if not text:
            return {}

        search_text = text if self.case_sensitive else text.lower()
        scores = {}

        for topic, keywords in self.topics.items():
            count = 0
            for keyword in keywords:
                kw = keyword if self.case_sensitive else keyword.lower()
                count += search_text.count(kw)
            if count > 0:
                scores[topic] = count

        return scores

    def add_topic(self, name: str, keywords: list[str]):
        """Add a new topic."""
        self.topics[name] = keywords

    def remove_topic(self, name: str):
        """Remove a topic."""
        self.topics.pop(name, None)

    def get_topics(self) -> list[str]:
        """Get list of all topic names."""
        return list(self.topics.keys())
