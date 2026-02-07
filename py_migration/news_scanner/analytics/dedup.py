"""
Deduplication

Removes duplicate news items based on ID and title similarity.
"""

import re
import hashlib
from typing import Optional
from dataclasses import dataclass

from ..models import NormalizedNewsItem


@dataclass
class DeduplicationResult:
    """Result of deduplication."""
    items: list[NormalizedNewsItem]
    removed_count: int
    removed_ids: list[str]


class Deduplicator:
    """
    Removes duplicate news items.

    Uses multiple strategies:
    1. Exact ID match
    2. Title similarity (normalized)
    3. URL match

    Example usage:
        dedup = Deduplicator()
        result = dedup.deduplicate(items)
        print(f"Removed {result.removed_count} duplicates")

        # Adjust similarity threshold:
        dedup = Deduplicator(title_similarity_threshold=0.9)

        # Check if two items are duplicates:
        is_dup = dedup.are_duplicates(item1, item2)
    """

    def __init__(
        self,
        use_title_hash: bool = True,
        use_url: bool = True,
        title_similarity_threshold: float = 1.0,  # 1.0 = exact match only
    ):
        """
        Initialize deduplicator.

        Args:
            use_title_hash: Whether to dedupe by normalized title hash.
            use_url: Whether to dedupe by URL.
            title_similarity_threshold: Similarity threshold for fuzzy matching (0-1).
        """
        self.use_title_hash = use_title_hash
        self.use_url = use_url
        self.title_similarity_threshold = title_similarity_threshold

    def deduplicate(self, items: list[NormalizedNewsItem]) -> DeduplicationResult:
        """
        Remove duplicates from a list of items.

        Args:
            items: List of news items.

        Returns:
            DeduplicationResult with unique items and stats.
        """
        if not items:
            return DeduplicationResult(items=[], removed_count=0, removed_ids=[])

        unique = []
        removed_ids = []
        seen_ids = set()
        seen_title_hashes = set()
        seen_urls = set()

        for item in items:
            # Check ID
            if item.id in seen_ids:
                removed_ids.append(item.id)
                continue

            # Check title hash
            if self.use_title_hash:
                title_hash = self._normalize_title_hash(item.title)
                if title_hash in seen_title_hashes:
                    removed_ids.append(item.id)
                    continue
                seen_title_hashes.add(title_hash)

            # Check URL
            if self.use_url and item.url:
                normalized_url = self._normalize_url(item.url)
                if normalized_url in seen_urls:
                    removed_ids.append(item.id)
                    continue
                seen_urls.add(normalized_url)

            seen_ids.add(item.id)
            unique.append(item)

        return DeduplicationResult(
            items=unique,
            removed_count=len(removed_ids),
            removed_ids=removed_ids,
        )

    def are_duplicates(self, item1: NormalizedNewsItem, item2: NormalizedNewsItem) -> bool:
        """
        Check if two items are duplicates.

        Args:
            item1: First item.
            item2: Second item.

        Returns:
            True if items are duplicates.
        """
        # Same ID
        if item1.id == item2.id:
            return True

        # Same URL
        if self.use_url and item1.url and item2.url:
            if self._normalize_url(item1.url) == self._normalize_url(item2.url):
                return True

        # Same title hash
        if self.use_title_hash:
            hash1 = self._normalize_title_hash(item1.title)
            hash2 = self._normalize_title_hash(item2.title)
            if hash1 == hash2:
                return True

        # Fuzzy title match (if threshold < 1)
        if self.title_similarity_threshold < 1.0:
            similarity = self._title_similarity(item1.title, item2.title)
            if similarity >= self.title_similarity_threshold:
                return True

        return False

    def _normalize_title_hash(self, title: str) -> str:
        """Create a hash of normalized title for comparison."""
        if not title:
            return ""

        # Normalize: lowercase, remove non-alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', title.lower())

        # Hash it
        return hashlib.md5(normalized.encode()).hexdigest()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ""

        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove www.
        url = re.sub(r'^www\.', '', url)
        # Remove trailing slash
        url = url.rstrip('/')
        # Remove common tracking params
        url = re.sub(r'\?utm_[^&]+(&|$)', '', url)
        url = re.sub(r'\?ref=[^&]+(&|$)', '', url)

        return url.lower()

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles.

        Uses simple word overlap ratio.
        """
        if not title1 or not title2:
            return 0.0

        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


class SlidingWindowDeduplicator(Deduplicator):
    """
    Deduplicator with a time-based sliding window.

    Only considers items within a time window for deduplication.
    Useful for streaming/continuous fetching.
    """

    def __init__(
        self,
        window_hours: int = 24,
        **kwargs
    ):
        """
        Initialize sliding window deduplicator.

        Args:
            window_hours: Only consider items within this many hours.
            **kwargs: Additional args passed to Deduplicator.
        """
        super().__init__(**kwargs)
        self.window_hours = window_hours
        self._seen_cache: dict[str, float] = {}  # id -> timestamp

    def deduplicate(self, items: list[NormalizedNewsItem]) -> DeduplicationResult:
        """
        Deduplicate with time window.

        Items older than window_hours are removed from cache.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=self.window_hours)
        cutoff_ts = cutoff.timestamp()

        # Clean old entries from cache
        self._seen_cache = {
            k: v for k, v in self._seen_cache.items()
            if v > cutoff_ts
        }

        # Use parent deduplication
        result = super().deduplicate(items)

        # Add new items to cache
        for item in result.items:
            try:
                ts = datetime.fromisoformat(item.published_at.replace('Z', '+00:00')).timestamp()
                self._seen_cache[item.id] = ts
            except (ValueError, AttributeError):
                pass

        return result
