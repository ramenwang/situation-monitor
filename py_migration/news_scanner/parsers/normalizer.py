"""
News item normalizer.

Ensures all fields are properly set and enriched.
"""

from typing import Optional

from ..models import NormalizedNewsItem, NewsMetadata
from ..analytics import TopicDetector, AlertDetector, TickerExtractor, RegionDetector
from ..utils import now_iso, extract_domain
from .text import clean_text, extract_summary


class Normalizer:
    """
    Normalizes news items.

    Ensures all required fields are set and enriches with analytics.

    Example usage:
        normalizer = Normalizer()
        item = normalizer.normalize(partial_item)

        # With custom analyzers:
        normalizer = Normalizer(
            topic_detector=MyTopicDetector(),
            alert_detector=MyAlertDetector()
        )
    """

    def __init__(
        self,
        topic_detector: Optional[TopicDetector] = None,
        alert_detector: Optional[AlertDetector] = None,
        ticker_extractor: Optional[TickerExtractor] = None,
        region_detector: Optional[RegionDetector] = None,
    ):
        """
        Initialize normalizer with analyzers.

        Args:
            topic_detector: Custom topic detector.
            alert_detector: Custom alert detector.
            ticker_extractor: Custom ticker extractor.
            region_detector: Custom region detector.
        """
        self.topic_detector = topic_detector or TopicDetector()
        self.alert_detector = alert_detector or AlertDetector()
        self.ticker_extractor = ticker_extractor or TickerExtractor()
        self.region_detector = region_detector or RegionDetector()

    def normalize(self, item: NormalizedNewsItem) -> NormalizedNewsItem:
        """
        Normalize a news item.

        - Cleans text fields
        - Extracts summary if missing
        - Detects topics, tickers, alerts, regions
        - Ensures all required fields are set

        Args:
            item: News item to normalize.

        Returns:
            Normalized news item.
        """
        # Clean text fields
        title = clean_text(item.title)
        summary = clean_text(item.summary) if item.summary else ""
        content = clean_text(item.content_text) if item.content_text else ""

        # Combine for analysis
        full_text = f"{title} {summary} {content}"

        # Extract/detect if not already set
        topics = item.topics if item.topics else self.topic_detector.detect(full_text)
        tickers = item.tickers if item.tickers else self.ticker_extractor.extract(full_text)

        # Always run alert detection on title
        alert = self.alert_detector.detect(title)

        # Detect region
        region = item.metadata.region if item.metadata and item.metadata.region else \
                 self.region_detector.detect(full_text)

        # Create metadata
        metadata = NewsMetadata(
            category=item.metadata.category if item.metadata else None,
            is_alert=alert.is_alert,
            alert_keyword=alert.keyword,
            region=region,
            domain=item.metadata.domain if item.metadata else extract_domain(item.url),
            image_url=item.metadata.image_url if item.metadata else None,
            raw=item.metadata.raw if item.metadata else None,
        )

        return NormalizedNewsItem(
            id=item.id,
            source=item.source or extract_domain(item.url),
            url=item.url,
            title=title,
            published_at=item.published_at or now_iso(),
            fetched_at=item.fetched_at or now_iso(),
            authors=item.authors or [],
            summary=summary or extract_summary(content),
            content_text=content,
            tickers=tickers,
            topics=topics,
            language=item.language or "en",
            metadata=metadata,
        )

    def normalize_many(self, items: list[NormalizedNewsItem]) -> list[NormalizedNewsItem]:
        """
        Normalize multiple items.

        Args:
            items: List of items to normalize.

        Returns:
            List of normalized items.
        """
        return [self.normalize(item) for item in items]
