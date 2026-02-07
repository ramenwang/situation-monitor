"""
RSS Feed Connector

Fetches and parses RSS/Atom feeds from various news sources.
"""

import asyncio
import re
from typing import Optional
from urllib.parse import quote

import aiohttp

from .base import BaseConnector
from ..models import NormalizedNewsItem, NewsMetadata, FeedSource
from ..utils import (
    config, logger, generate_id, parse_rss_date, now_iso, strip_html
)
from ..utils.config import FEEDS, INTEL_SOURCES
from ..analytics import TopicDetector, AlertDetector, TickerExtractor


class RSSConnector(BaseConnector):
    """
    Connector for RSS/Atom feeds.

    Example usage:
        connector = RSSConnector()

        # Fetch single category
        items = await connector.fetch_category("finance")

        # Fetch all categories
        items = await connector.fetch()

        # Fetch intel sources
        items = await connector.fetch_intel()

        # Fetch custom feed
        items = await connector.fetch_feed(
            FeedSource("My Feed", "https://example.com/rss.xml", "tech")
        )
    """

    def __init__(
        self,
        cors_proxies: Optional[list[str]] = None,
        timeout: int = 12,
        use_proxy: bool = True,
    ):
        """
        Initialize RSS connector.

        Args:
            cors_proxies: List of CORS proxy URLs (for browser env).
            timeout: Request timeout in seconds.
            use_proxy: Whether to use CORS proxy.
        """
        self.cors_proxies = cors_proxies or config.cors_proxies
        self.timeout = timeout
        self.use_proxy = use_proxy

        # Analytics (modular)
        self.topic_detector = TopicDetector()
        self.alert_detector = AlertDetector()
        self.ticker_extractor = TickerExtractor()

    async def fetch(
        self,
        categories: Optional[list[str]] = None,
        **kwargs
    ) -> list[NormalizedNewsItem]:
        """
        Fetch news from all categories.

        Args:
            categories: List of categories to fetch. Defaults to all.

        Returns:
            List of normalized news items.
        """
        if categories is None:
            categories = list(FEEDS.keys())

        all_items = []

        for category in categories:
            items = await self.fetch_category(category, **kwargs)
            all_items.extend(items)

        return all_items

    async def fetch_category(self, category: str, **kwargs) -> list[NormalizedNewsItem]:
        """
        Fetch all feeds for a category.

        Args:
            category: News category.

        Returns:
            List of normalized news items.
        """
        feeds = FEEDS.get(category, [])
        if not feeds:
            logger.debug(f"No RSS feeds for category: {category}")
            return []

        all_items = []

        for i, feed in enumerate(feeds):
            if i > 0:
                await asyncio.sleep(config.delay_between_requests)

            items = await self.fetch_feed(feed)
            all_items.extend(items)

        return all_items

    async def fetch_intel(self) -> list[NormalizedNewsItem]:
        """
        Fetch intel sources (think tanks, OSINT, etc.)

        Returns:
            List of normalized news items.
        """
        all_items = []

        for i, source in enumerate(INTEL_SOURCES):
            if i > 0:
                await asyncio.sleep(config.delay_between_requests)

            items = await self.fetch_feed(source)

            # Add intel metadata
            for item in items:
                item.metadata.raw = {
                    **(item.metadata.raw or {}),
                    "intel_type": source.source_type,
                    "intel_topics": source.topics,
                }

            all_items.extend(items)

        return all_items

    async def fetch_feed(self, source: FeedSource) -> list[NormalizedNewsItem]:
        """
        Fetch a single RSS feed.

        Args:
            source: Feed source configuration.

        Returns:
            List of normalized news items.
        """
        logger.debug(f"Fetching RSS {source.name}: {source.url}")

        xml = await self._fetch_with_proxy(source.url)
        if not xml:
            logger.warning(f"RSS {source.name}: Failed to fetch")
            return []

        items = self._parse_rss(xml)
        logger.info(f"RSS {source.name}: {len(items)} items")

        return [
            self._transform_item(item, source)
            for item in items
        ]

    async def _fetch_with_proxy(self, url: str) -> Optional[str]:
        """Fetch URL with CORS proxy fallback."""
        proxies = self.cors_proxies if self.use_proxy else [""]

        for proxy in proxies:
            try:
                fetch_url = f"{proxy}{quote(url, safe='')}" if proxy else url

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        fetch_url,
                        timeout=self.timeout,
                        headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"}
                    ) as response:
                        if response.status != 200:
                            logger.debug(f"RSS proxy failed ({response.status}): {proxy}")
                            continue

                        text = await response.text()

                        # Validate XML
                        if not text or '<!DOCTYPE html>' in text.lower():
                            continue

                        return text

            except asyncio.TimeoutError:
                logger.debug(f"RSS proxy timeout: {proxy}")
            except aiohttp.ClientError as e:
                logger.debug(f"RSS proxy error: {proxy} - {e}")

        return None

    def _parse_rss(self, xml: str) -> list[dict]:
        """Parse RSS/Atom XML to list of items."""
        items = []

        # Match <item> or <entry> tags
        item_pattern = re.compile(r'<(?:item|entry)[\s>](.*?)</(?:item|entry)>', re.DOTALL | re.IGNORECASE)

        for match in item_pattern.finditer(xml):
            item_xml = match.group(1)
            item = {}

            # Title
            title_match = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_xml, re.DOTALL | re.IGNORECASE)
            if title_match:
                item['title'] = strip_html(title_match.group(1).strip())

            # Link (RSS or Atom style)
            link_href = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', item_xml, re.IGNORECASE)
            link_content = re.search(r'<link[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item_xml, re.DOTALL | re.IGNORECASE)
            item['link'] = (link_href.group(1) if link_href else None) or \
                           (link_content.group(1).strip() if link_content else None)

            # Description/Summary
            desc_match = re.search(r'<(?:description|summary)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:description|summary)>', item_xml, re.DOTALL | re.IGNORECASE)
            if desc_match:
                item['description'] = strip_html(desc_match.group(1).strip())

            # Content
            content_match = re.search(r'<(?:content:encoded|content)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:content:encoded|content)>', item_xml, re.DOTALL | re.IGNORECASE)
            if content_match:
                item['content'] = strip_html(content_match.group(1).strip())

            # Date
            date_match = re.search(r'<(?:pubDate|updated|published)[^>]*>(.*?)</(?:pubDate|updated|published)>', item_xml, re.DOTALL | re.IGNORECASE)
            if date_match:
                item['pubDate'] = date_match.group(1).strip()

            # Author
            author_match = re.search(r'<(?:author|dc:creator|creator)[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</(?:author|dc:creator|creator)>', item_xml, re.DOTALL | re.IGNORECASE)
            if author_match:
                item['author'] = strip_html(author_match.group(1).strip())

            if item.get('title') or item.get('link'):
                items.append(item)

        return items

    def _transform_item(self, item: dict, source: FeedSource) -> NormalizedNewsItem:
        """Transform RSS item to normalized schema."""
        title = item.get("title", "")
        description = item.get("description", "")
        content = item.get("content", "")
        full_text = f"{title} {description} {content}"

        # Use modular analytics
        topics = self.topic_detector.detect(full_text)
        alert = self.alert_detector.detect(title)
        tickers = self.ticker_extractor.extract(full_text)

        url = item.get("link", "")
        author = item.get("author")

        return NormalizedNewsItem(
            id=generate_id(url or title, source.name),
            source=source.name,
            url=url,
            title=title,
            published_at=parse_rss_date(item.get("pubDate", "")),
            fetched_at=now_iso(),
            authors=[author] if author else [],
            summary=description,
            content_text=content or description,
            tickers=tickers,
            topics=topics,
            language="en",
            metadata=NewsMetadata(
                category=source.category,
                is_alert=alert.is_alert,
                alert_keyword=alert.keyword,
                raw=item,
            ),
        )
