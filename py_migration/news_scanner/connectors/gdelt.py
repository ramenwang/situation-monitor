"""
GDELT News API Connector

Fetches news from the Global Database of Events, Language, and Tone (GDELT).
https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

import asyncio
from typing import Optional
from urllib.parse import urlencode

import aiohttp

from .base import BaseConnector
from ..models import NormalizedNewsItem, NewsMetadata
from ..utils import config, logger, generate_id, parse_gdelt_date, now_iso
from ..utils.config import GDELT_QUERIES
from ..analytics import TopicDetector, AlertDetector


class GdeltConnector(BaseConnector):
    """
    Connector for GDELT news API.

    Example usage:
        connector = GdeltConnector()

        # Fetch single category
        items = await connector.fetch_category("finance")

        # Fetch multiple categories
        items = await connector.fetch(categories=["finance", "tech"])

        # With options
        items = await connector.fetch(
            categories=["finance"],
            max_records=50,
            timespan="24h"
        )
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 15,
        max_records: int = 20,
        timespan: str = "7d",
        language: str = "english",
    ):
        """
        Initialize GDELT connector.

        Args:
            base_url: GDELT API base URL.
            timeout: Request timeout in seconds.
            max_records: Max articles per request (max 250).
            timespan: Time range for articles (e.g., "7d", "24h").
            language: Language filter.
        """
        self.base_url = base_url or config.gdelt_base_url
        self.timeout = timeout
        self.max_records = min(max_records, 250)
        self.timespan = timespan
        self.language = language

        # Analytics (modular)
        self.topic_detector = TopicDetector()
        self.alert_detector = AlertDetector()

    async def fetch(
        self,
        categories: Optional[list[str]] = None,
        **kwargs
    ) -> list[NormalizedNewsItem]:
        """
        Fetch news from all specified categories.

        Args:
            categories: List of categories to fetch. Defaults to all.

        Returns:
            List of normalized news items.
        """
        if categories is None:
            categories = list(GDELT_QUERIES.keys())

        all_items = []

        for i, category in enumerate(categories):
            if i > 0:
                await asyncio.sleep(config.delay_between_requests)

            items = await self.fetch_category(category, **kwargs)
            all_items.extend(items)

        return all_items

    async def fetch_category(
        self,
        category: str,
        max_records: Optional[int] = None,
        timespan: Optional[str] = None,
        **kwargs
    ) -> list[NormalizedNewsItem]:
        """
        Fetch news for a specific category.

        Args:
            category: News category.
            max_records: Override default max records.
            timespan: Override default timespan.

        Returns:
            List of normalized news items.
        """
        query = GDELT_QUERIES.get(category)
        if not query:
            logger.warning(f"Unknown GDELT category: {category}")
            return []

        # Build query
        full_query = f"{query} sourcelang:{self.language}"
        params = {
            "query": full_query,
            "timespan": timespan or self.timespan,
            "mode": "artlist",
            "maxrecords": max_records or self.max_records,
            "format": "json",
            "sort": "date",
        }

        url = f"{self.base_url}/api/v2/doc/doc?{urlencode(params)}"
        logger.debug(f"Fetching GDELT {category}: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        logger.warning(f"GDELT {category}: HTTP {response.status}")
                        return []

                    content_type = response.headers.get('content-type', '')
                    if 'json' not in content_type:
                        logger.warning(f"GDELT {category}: Non-JSON response")
                        return []

                    data = await response.json()

            articles = data.get("articles", [])
            logger.info(f"GDELT {category}: {len(articles)} articles")

            return [
                self._transform_article(article, category)
                for article in articles
            ]

        except asyncio.TimeoutError:
            logger.error(f"GDELT {category}: Timeout")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"GDELT {category}: {e}")
            return []
        except Exception as e:
            logger.error(f"GDELT {category}: {e}")
            return []

    def _transform_article(self, article: dict, category: str) -> NormalizedNewsItem:
        """Transform GDELT article to normalized schema."""
        title = article.get("title", "")
        url = article.get("url", "")

        # Use modular analytics
        topics = self.topic_detector.detect(title)
        alert = self.alert_detector.detect(title)

        return NormalizedNewsItem(
            id=generate_id(url, f"gdelt-{category}"),
            source=article.get("domain", "GDELT"),
            url=url,
            title=title,
            published_at=parse_gdelt_date(article.get("seendate", "")),
            fetched_at=now_iso(),
            authors=[],
            summary="",
            content_text="",
            tickers=[],
            topics=topics,
            language=article.get("language", "en"),
            metadata=NewsMetadata(
                category=category,
                is_alert=alert.is_alert,
                alert_keyword=alert.keyword,
                domain=article.get("domain"),
                image_url=article.get("socialimage"),
                raw=article,
            ),
        )
