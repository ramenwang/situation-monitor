"""
Tests for analytics modules.
"""

import pytest
from news_scanner.analytics import (
    TopicDetector,
    AlertDetector,
    TickerExtractor,
    RegionDetector,
    Deduplicator,
    SentimentAnalyzer,
)
from news_scanner.analytics.alerts import Sentiment
from news_scanner.models import NormalizedNewsItem, NewsMetadata


class TestTopicDetector:
    def test_detect_single_topic(self):
        detector = TopicDetector()
        topics = detector.detect("Federal Reserve raises interest rates")
        assert "FINANCE" in topics

    def test_detect_multiple_topics(self):
        detector = TopicDetector()
        topics = detector.detect("Cyber attack on military base causes stock crash")
        assert "CYBER" in topics
        assert "CONFLICT" in topics or "FINANCE" in topics

    def test_detect_no_topics(self):
        detector = TopicDetector()
        topics = detector.detect("The weather is nice today")
        assert topics == []

    def test_custom_topics(self):
        detector = TopicDetector(topics={"CUSTOM": ["foo", "bar"]})
        topics = detector.detect("This contains foo keyword")
        assert topics == ["CUSTOM"]

    def test_detect_with_scores(self):
        detector = TopicDetector()
        scores = detector.detect_with_scores("bitcoin ethereum crypto rally")
        assert "CRYPTO" in scores
        assert scores["CRYPTO"] >= 3

    def test_add_topic(self):
        detector = TopicDetector()
        detector.add_topic("BIOTECH", ["gene", "therapy"])
        topics = detector.detect("New gene therapy approved")
        assert "BIOTECH" in topics


class TestAlertDetector:
    def test_detect_alert(self):
        detector = AlertDetector()
        result = detector.detect("Russia launches missile strike")
        assert result.is_alert is True
        assert result.keyword == "missile"
        assert result.severity == "high"

    def test_no_alert(self):
        detector = AlertDetector()
        result = detector.detect("Stock market opens higher")
        assert result.is_alert is False
        assert result.keyword is None

    def test_critical_severity(self):
        detector = AlertDetector()
        result = detector.detect("Nuclear weapons treaty signed")
        assert result.is_alert is True
        assert result.severity == "critical"

    def test_detect_all(self):
        detector = AlertDetector()
        results = detector.detect_all("Military troops deploy missiles")
        assert len(results) >= 2
        keywords = [r.keyword for r in results]
        assert "military" in keywords or "troops" in keywords

    def test_custom_keywords(self):
        detector = AlertDetector(keywords={"custom_alert": "high"})
        result = detector.detect("This is a custom_alert test")
        assert result.is_alert is True
        assert result.keyword == "custom_alert"


class TestTickerExtractor:
    def test_extract_dollar_tickers(self):
        extractor = TickerExtractor()
        tickers = extractor.extract("$AAPL and $GOOGL are up today")
        assert "AAPL" in tickers
        assert "GOOGL" in tickers

    def test_extract_crypto(self):
        extractor = TickerExtractor()
        tickers = extractor.extract("Bitcoin BTC and Ethereum ETH surge")
        assert "BTC" in tickers
        assert "ETH" in tickers

    def test_exclude_common_words(self):
        extractor = TickerExtractor()
        tickers = extractor.extract("The CEO said AI will change IT")
        assert "CEO" not in tickers
        assert "AI" not in tickers
        assert "IT" not in tickers

    def test_extract_with_types(self):
        extractor = TickerExtractor()
        matches = extractor.extract_with_types("$AAPL up, BTC surging")
        assert len(matches) == 2
        types = {m.symbol: m.ticker_type for m in matches}
        assert types["AAPL"] == "stock"
        assert types["BTC"] == "crypto"


class TestRegionDetector:
    def test_detect_region(self):
        detector = RegionDetector()
        region = detector.detect("Tensions rise in Taiwan Strait")
        assert region == "APAC"

    def test_detect_multiple_regions(self):
        detector = RegionDetector()
        regions = detector.detect_all("US sanctions on Russia over Ukraine")
        assert "AMERICAS" in regions
        assert "EUROPE" in regions or "RUSSIA_CIS" in regions

    def test_no_region(self):
        detector = RegionDetector()
        region = detector.detect("The weather is nice")
        assert region is None

    def test_detect_with_keywords(self):
        detector = RegionDetector()
        results = detector.detect_with_keywords("NATO and EU discuss Ukraine")
        assert "EUROPE" in results
        assert "nato" in results["EUROPE"] or "eu" in results["EUROPE"]


class TestDeduplicator:
    def create_item(self, id: str, title: str, url: str = "") -> NormalizedNewsItem:
        return NormalizedNewsItem(
            id=id,
            source="Test",
            url=url or f"https://example.com/{id}",
            title=title,
            published_at="2024-01-01T00:00:00Z",
            fetched_at="2024-01-01T00:00:00Z",
        )

    def test_dedupe_by_id(self):
        dedup = Deduplicator()
        items = [
            self.create_item("1", "Title A"),
            self.create_item("1", "Title A"),  # Duplicate ID
            self.create_item("2", "Title B"),
        ]
        result = dedup.deduplicate(items)
        assert len(result.items) == 2
        assert result.removed_count == 1

    def test_dedupe_by_title(self):
        dedup = Deduplicator()
        items = [
            self.create_item("1", "Breaking News: Market Crash"),
            self.create_item("2", "Breaking News: Market Crash"),  # Same title
            self.create_item("3", "Different Title"),
        ]
        result = dedup.deduplicate(items)
        assert len(result.items) == 2
        assert result.removed_count == 1

    def test_are_duplicates(self):
        dedup = Deduplicator()
        item1 = self.create_item("1", "Same Title")
        item2 = self.create_item("2", "Same Title")
        assert dedup.are_duplicates(item1, item2) is True

        item3 = self.create_item("3", "Different Title")
        assert dedup.are_duplicates(item1, item3) is False


class TestSentimentAnalyzer:
    def test_positive_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Stock surges on strong earnings, rally continues")
        assert result.sentiment == Sentiment.POSITIVE
        assert result.score > 0

    def test_negative_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Market crashes amid recession fears, stocks plunge")
        assert result.sentiment == Sentiment.NEGATIVE
        assert result.score < 0

    def test_neutral_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("The meeting was held yesterday")
        assert result.sentiment == Sentiment.NEUTRAL
        assert result.score == 0

    def test_mixed_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Stocks rally despite crash concerns")
        assert result.sentiment == Sentiment.MIXED

    def test_is_positive(self):
        analyzer = SentimentAnalyzer()
        assert analyzer.is_positive("Strong rally in tech stocks") is True
        assert analyzer.is_positive("Market crashes") is False
