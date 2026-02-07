"""
Pipeline filters.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from ..models import NormalizedNewsItem


@dataclass
class FilterConfig:
    """
    Configuration for filtering news items.

    Example usage:
        config = FilterConfig(
            categories=["finance", "tech"],
            topics=["CRYPTO", "FINANCE"],
            include_keywords=["bitcoin", "ethereum"],
            exclude_keywords=["spam"],
            max_age_hours=24
        )
        filtered = filter_items(items, config)
    """
    # Category filter
    categories: Optional[list[str]] = None

    # Region filter
    regions: Optional[list[str]] = None

    # Topic filter
    topics: Optional[list[str]] = None

    # Keyword filters
    include_keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None

    # Time filter
    max_age_hours: Optional[int] = None

    # Alert filter
    alerts_only: bool = False

    # Source filter
    sources: Optional[list[str]] = None
    exclude_sources: Optional[list[str]] = None

    # Ticker filter
    tickers: Optional[list[str]] = None


def filter_items(
    items: list[NormalizedNewsItem],
    config: FilterConfig
) -> list[NormalizedNewsItem]:
    """
    Filter news items based on configuration.

    Args:
        items: List of items to filter.
        config: Filter configuration.

    Returns:
        Filtered list of items.
    """
    filtered = []

    # Pre-calculate cutoff time if needed
    cutoff_time = None
    if config.max_age_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=config.max_age_hours)

    for item in items:
        # Category filter
        if config.categories:
            category = item.metadata.category if item.metadata else None
            if category not in config.categories:
                continue

        # Region filter
        if config.regions:
            region = item.metadata.region if item.metadata else None
            if region not in config.regions:
                continue

        # Topic filter
        if config.topics:
            if not any(t in config.topics for t in item.topics):
                continue

        # Include keywords
        if config.include_keywords:
            text = f"{item.title} {item.summary}".lower()
            if not any(kw.lower() in text for kw in config.include_keywords):
                continue

        # Exclude keywords
        if config.exclude_keywords:
            text = f"{item.title} {item.summary}".lower()
            if any(kw.lower() in text for kw in config.exclude_keywords):
                continue

        # Age filter
        if cutoff_time:
            try:
                item_time = datetime.fromisoformat(
                    item.published_at.replace('Z', '+00:00')
                ).replace(tzinfo=None)
                if item_time < cutoff_time:
                    continue
            except (ValueError, AttributeError):
                pass

        # Alerts only
        if config.alerts_only:
            if not (item.metadata and item.metadata.is_alert):
                continue

        # Source filter
        if config.sources:
            if item.source not in config.sources:
                continue

        # Exclude sources
        if config.exclude_sources:
            if item.source in config.exclude_sources:
                continue

        # Ticker filter
        if config.tickers:
            if not any(t in config.tickers for t in item.tickers):
                continue

        filtered.append(item)

    return filtered


class FilterPipeline:
    """
    Chainable filter pipeline.

    Example usage:
        pipeline = FilterPipeline()
        pipeline.add_category_filter(["finance"])
        pipeline.add_topic_filter(["CRYPTO"])
        pipeline.add_age_filter(hours=24)

        filtered = pipeline.apply(items)
    """

    def __init__(self):
        self._filters: list[callable] = []

    def add_filter(self, filter_fn: callable) -> "FilterPipeline":
        """Add a custom filter function."""
        self._filters.append(filter_fn)
        return self

    def add_category_filter(self, categories: list[str]) -> "FilterPipeline":
        """Add category filter."""
        def fn(item):
            category = item.metadata.category if item.metadata else None
            return category in categories
        self._filters.append(fn)
        return self

    def add_topic_filter(self, topics: list[str]) -> "FilterPipeline":
        """Add topic filter."""
        def fn(item):
            return any(t in topics for t in item.topics)
        self._filters.append(fn)
        return self

    def add_age_filter(self, hours: int) -> "FilterPipeline":
        """Add age filter."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        def fn(item):
            try:
                item_time = datetime.fromisoformat(
                    item.published_at.replace('Z', '+00:00')
                ).replace(tzinfo=None)
                return item_time >= cutoff
            except:
                return True
        self._filters.append(fn)
        return self

    def add_keyword_filter(self, keywords: list[str], exclude: bool = False) -> "FilterPipeline":
        """Add keyword filter."""
        def fn(item):
            text = f"{item.title} {item.summary}".lower()
            has_keyword = any(kw.lower() in text for kw in keywords)
            return not has_keyword if exclude else has_keyword
        self._filters.append(fn)
        return self

    def add_alert_filter(self) -> "FilterPipeline":
        """Add alert-only filter."""
        def fn(item):
            return item.metadata and item.metadata.is_alert
        self._filters.append(fn)
        return self

    def apply(self, items: list[NormalizedNewsItem]) -> list[NormalizedNewsItem]:
        """Apply all filters to items."""
        result = items
        for filter_fn in self._filters:
            result = [item for item in result if filter_fn(item)]
        return result
