"""
Alert Detection

Detects high-priority alert keywords in news text.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AlertResult:
    """Result of alert detection."""
    is_alert: bool
    keyword: Optional[str] = None
    severity: str = "normal"  # "normal", "elevated", "high", "critical"


# Default alert keywords with severity levels
DEFAULT_ALERT_KEYWORDS: dict[str, str] = {
    # Critical
    "nuclear": "critical",
    "assassination": "critical",
    "coup": "critical",
    "martial law": "critical",
    "war declared": "critical",

    # High
    "war": "high",
    "invasion": "high",
    "missile": "high",
    "bomb": "high",
    "terrorist": "high",
    "hostage": "high",
    "casualties": "high",

    # Elevated
    "military": "elevated",
    "sanctions": "elevated",
    "attack": "elevated",
    "troops": "elevated",
    "conflict": "elevated",
    "strike": "elevated",
    "ceasefire": "elevated",
    "treaty": "elevated",
    "nato": "elevated",
    "emergency": "elevated",
    "evacuation": "elevated",
}


class AlertDetector:
    """
    Detects alert keywords in text.

    Example usage:
        detector = AlertDetector()
        result = detector.detect("Russia launches missile strike")
        # Returns: AlertResult(is_alert=True, keyword="missile", severity="high")

        # Custom keywords:
        detector = AlertDetector(keywords={"custom_alert": "high"})

        # Add keywords at runtime:
        detector.add_keyword("earthquake", "elevated")
    """

    def __init__(
        self,
        keywords: Optional[dict[str, str]] = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize alert detector.

        Args:
            keywords: Dict of keyword -> severity. If None, uses defaults.
            case_sensitive: Whether to match case-sensitively.
        """
        self.keywords = keywords if keywords is not None else DEFAULT_ALERT_KEYWORDS.copy()
        self.case_sensitive = case_sensitive

        # Sort by severity (critical first) for priority matching
        severity_order = {"critical": 0, "high": 1, "elevated": 2, "normal": 3}
        self._sorted_keywords = sorted(
            self.keywords.items(),
            key=lambda x: severity_order.get(x[1], 3)
        )

    def detect(self, text: str) -> AlertResult:
        """
        Detect alert keywords in text.

        Args:
            text: Text to analyze.

        Returns:
            AlertResult with is_alert, keyword, and severity.
        """
        if not text:
            return AlertResult(is_alert=False)

        search_text = text if self.case_sensitive else text.lower()

        for keyword, severity in self._sorted_keywords:
            kw = keyword if self.case_sensitive else keyword.lower()
            if kw in search_text:
                return AlertResult(is_alert=True, keyword=keyword, severity=severity)

        return AlertResult(is_alert=False)

    def detect_all(self, text: str) -> list[AlertResult]:
        """
        Detect all alert keywords in text.

        Args:
            text: Text to analyze.

        Returns:
            List of AlertResults for all matches.
        """
        if not text:
            return []

        search_text = text if self.case_sensitive else text.lower()
        results = []

        for keyword, severity in self._sorted_keywords:
            kw = keyword if self.case_sensitive else keyword.lower()
            if kw in search_text:
                results.append(AlertResult(is_alert=True, keyword=keyword, severity=severity))

        return results

    def add_keyword(self, keyword: str, severity: str = "elevated"):
        """Add a new alert keyword."""
        self.keywords[keyword] = severity
        # Re-sort
        severity_order = {"critical": 0, "high": 1, "elevated": 2, "normal": 3}
        self._sorted_keywords = sorted(
            self.keywords.items(),
            key=lambda x: severity_order.get(x[1], 3)
        )

    def remove_keyword(self, keyword: str):
        """Remove an alert keyword."""
        self.keywords.pop(keyword, None)
        self._sorted_keywords = [(k, v) for k, v in self._sorted_keywords if k != keyword]

    def get_keywords(self) -> dict[str, str]:
        """Get all keywords with their severities."""
        return self.keywords.copy()

    def get_by_severity(self, severity: str) -> list[str]:
        """Get keywords of a specific severity level."""
        return [k for k, v in self.keywords.items() if v == severity]
