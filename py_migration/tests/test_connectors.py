"""
Tests for connectors (with mocked network).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from news_scanner.connectors import GdeltConnector, RSSConnector


class TestGdeltConnector:
    @pytest.mark.asyncio
    async def test_fetch_category(self):
        """Test GDELT category fetch with mocked response."""
        mock_response = {
            "articles": [
                {
                    "title": "Test Finance Article",
                    "url": "https://example.com/article1",
                    "seendate": "20240115T120000Z",
                    "domain": "example.com",
                    "socialimage": "https://example.com/image.jpg",
                },
                {
                    "title": "Another Tech Article",
                    "url": "https://example.com/article2",
                    "seendate": "20240115T110000Z",
                    "domain": "tech.com",
                },
            ]
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {"content-type": "application/json"}
            mock_resp.json = AsyncMock(return_value=mock_response)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = GdeltConnector()
            items = await connector.fetch_category("finance")

            assert len(items) == 2
            assert items[0].title == "Test Finance Article"
            assert items[0].source == "example.com"
            assert items[0].metadata.category == "finance"

    @pytest.mark.asyncio
    async def test_fetch_category_empty_response(self):
        """Test handling of empty GDELT response."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {"content-type": "application/json"}
            mock_resp.json = AsyncMock(return_value={})

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = GdeltConnector()
            items = await connector.fetch_category("politics")

            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_fetch_category_error(self):
        """Test handling of HTTP error."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 500

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = GdeltConnector()
            items = await connector.fetch_category("tech")

            assert len(items) == 0


class TestRSSConnector:
    SAMPLE_RSS = """
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Breaking News: Market Rally</title>
                <link>https://example.com/news/1</link>
                <description>Markets are up today.</description>
                <pubDate>Mon, 15 Jan 2024 12:00:00 +0000</pubDate>
                <dc:creator>John Doe</dc:creator>
            </item>
            <item>
                <title>Tech Company $AAPL Announces Layoffs</title>
                <link>https://example.com/news/2</link>
                <description>Major tech company cutting jobs.</description>
                <pubDate>Mon, 15 Jan 2024 11:00:00 +0000</pubDate>
            </item>
        </channel>
    </rss>
    """

    @pytest.mark.asyncio
    async def test_fetch_feed(self):
        """Test RSS feed fetch with mocked response."""
        from news_scanner.models import FeedSource

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.text = AsyncMock(return_value=self.SAMPLE_RSS)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = RSSConnector(use_proxy=False)
            source = FeedSource("Test Feed", "https://example.com/feed.xml", "finance")
            items = await connector.fetch_feed(source)

            assert len(items) == 2
            assert items[0].title == "Breaking News: Market Rally"
            assert items[0].source == "Test Feed"
            assert items[0].summary == "Markets are up today."

    @pytest.mark.asyncio
    async def test_ticker_extraction(self):
        """Test that tickers are extracted from RSS items."""
        from news_scanner.models import FeedSource

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.text = AsyncMock(return_value=self.SAMPLE_RSS)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = RSSConnector(use_proxy=False)
            source = FeedSource("Test Feed", "https://example.com/feed.xml", "tech")
            items = await connector.fetch_feed(source)

            # Second item mentions $AAPL
            assert "AAPL" in items[1].tickers

    @pytest.mark.asyncio
    async def test_fetch_error(self):
        """Test handling of fetch error."""
        from news_scanner.models import FeedSource

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 404

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_resp
            mock_ctx.__aexit__.return_value = None

            mock_session_inst = AsyncMock()
            mock_session_inst.get.return_value = mock_ctx
            mock_session_inst.__aenter__.return_value = mock_session_inst
            mock_session_inst.__aexit__.return_value = None
            mock_session.return_value = mock_session_inst

            connector = RSSConnector(use_proxy=False)
            source = FeedSource("Test Feed", "https://example.com/feed.xml", "finance")
            items = await connector.fetch_feed(source)

            assert len(items) == 0
