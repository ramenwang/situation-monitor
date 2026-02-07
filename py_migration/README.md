# Trading News Scanner (Python)

A modular Python news scanning and summarization toolkit for trading applications.

## Features

- **Modular Analytics**: Each analyzer (topics, alerts, tickers, regions, sentiment) is independent
- **Multiple Sources**: GDELT API, 30+ RSS feeds, 12+ intel sources
- **Extensible**: Easy to add new sources, analyzers, or storage backends
- **Async**: Built on asyncio for efficient concurrent fetching
- **Type-Safe**: Full type hints throughout

## Quick Start

### Installation

```bash
cd py_migration
pip install -r requirements.txt
```

### Run the Demo

```bash
python run_demo.py
```

With options:
```bash
# Only finance and tech
python run_demo.py --categories finance tech

# Alerts only
python run_demo.py --alerts-only

# Last 24 hours
python run_demo.py --max-age 24

# Skip certain sources
python run_demo.py --no-gdelt --no-intel
```

### Run Tests

```bash
pytest tests/ -v
```

## Architecture

```
news_scanner/
├── analytics/          # Modular analyzers
│   ├── topics.py       # Topic detection
│   ├── alerts.py       # Alert keyword detection
│   ├── tickers.py      # Stock/crypto ticker extraction
│   ├── regions.py      # Geographic region detection
│   ├── sentiment.py    # Sentiment analysis
│   └── dedup.py        # Deduplication
├── connectors/         # Data source connectors
│   ├── gdelt.py        # GDELT API
│   └── rss.py          # RSS/Atom feeds
├── parsers/            # Text processing
│   ├── text.py         # HTML cleaning, summarization
│   └── normalizer.py   # Item normalization
├── pipeline/           # Orchestration
│   ├── runner.py       # Main pipeline
│   └── filters.py      # Filtering logic
├── storage/            # Output adapters
│   ├── jsonl.py        # JSONL files
│   └── sqlite.py       # SQLite database
└── utils/              # Configuration, logging
    ├── config.py       # Feeds, keywords, settings
    ├── helpers.py      # Utility functions
    └── logger.py       # Logging
```

## Usage Examples

### Simple Pipeline

```python
import asyncio
from news_scanner import NewsPipeline, run_pipeline

async def main():
    result = await run_pipeline()
    print(f"Fetched {len(result.items)} items")

asyncio.run(main())
```

### Custom Pipeline

```python
from news_scanner import NewsPipeline
from news_scanner.pipeline import PipelineOptions, FilterConfig
from news_scanner.storage import SqliteStorage

async def main():
    options = PipelineOptions(
        categories=["finance", "tech"],
        use_intel=False,
        filter_config=FilterConfig(
            topics=["FINANCE", "CRYPTO"],
            max_age_hours=24
        ),
        storage=SqliteStorage("output/news.db")
    )

    pipeline = NewsPipeline(options)
    result = await pipeline.run()
```

### Using Individual Analyzers

```python
from news_scanner.analytics import (
    TopicDetector,
    AlertDetector,
    TickerExtractor,
    SentimentAnalyzer
)

# Topic detection
topic_detector = TopicDetector()
topics = topic_detector.detect("Federal Reserve raises interest rates")
# ["FINANCE"]

# Alert detection
alert_detector = AlertDetector()
alert = alert_detector.detect("Russia launches missile strike")
# AlertResult(is_alert=True, keyword="missile", severity="high")

# Ticker extraction
ticker_extractor = TickerExtractor()
tickers = ticker_extractor.extract("$AAPL and BTC are up today")
# ["AAPL", "BTC"]

# Sentiment analysis
sentiment = SentimentAnalyzer()
result = sentiment.analyze("Stock surges on strong earnings")
# SentimentResult(sentiment=POSITIVE, score=0.5, ...)
```

### Custom Topic Configuration

```python
from news_scanner.analytics import TopicDetector

# Add custom topics
detector = TopicDetector()
detector.add_topic("BIOTECH", ["gene", "therapy", "pharmaceutical", "fda approval"])
detector.add_topic("REAL_ESTATE", ["housing", "mortgage", "property", "rent"])

topics = detector.detect("FDA approves new gene therapy")
# ["BIOTECH"]
```

### Adding a New News Source

```python
from news_scanner.connectors import BaseConnector
from news_scanner.models import NormalizedNewsItem

class TwitterConnector(BaseConnector):
    async def fetch(self, **kwargs):
        # Fetch from Twitter API
        tweets = await self._fetch_tweets()

        return [
            NormalizedNewsItem(
                id=tweet["id"],
                source="Twitter",
                url=tweet["url"],
                title=tweet["text"][:100],
                # ... other fields
            )
            for tweet in tweets
        ]

    async def fetch_category(self, category, **kwargs):
        return await self.fetch(query=category)
```

### Query SQLite Storage

```python
from news_scanner.storage import SqliteStorage

storage = SqliteStorage("output/news.db")

# Get all alerts
alerts = storage.get_alerts(limit=50)

# Query by source
bbc_news = storage.get_by_source("BBC World")

# Custom query
crypto_news = storage.query(
    "json_extract(metadata, '$.category') = ?",
    ["finance"]
)

# Get stats
print(f"Total items: {storage.count()}")
print(f"Sources: {storage.get_sources()}")
```

## Output Schema

All items follow the normalized schema:

```python
@dataclass
class NormalizedNewsItem:
    id: str                    # Stable hash
    source: str                # "BBC World", "GDELT", etc.
    url: str                   # Article URL
    title: str                 # Headline
    published_at: str          # ISO8601
    fetched_at: str            # ISO8601
    authors: list[str]         # Author names
    summary: str               # Description
    content_text: str          # Full text if available
    tickers: list[str]         # ["AAPL", "BTC"]
    topics: list[str]          # ["FINANCE", "CRYPTO"]
    language: str              # "en"
    metadata: NewsMetadata     # Additional data
```

## Configuration

Environment variables:

```bash
# API Keys (optional)
FINNHUB_API_KEY=your_key
FRED_API_KEY=your_key

# CORS Proxies (for RSS in browser)
CORS_PROXY_PRIMARY=https://api.allorigins.win/raw?url=
CORS_PROXY_FALLBACK=https://corsproxy.io/?url=

# Settings
REQUEST_TIMEOUT=15
DELAY_BETWEEN_REQUESTS=0.5
OUTPUT_DIR=./output
DEBUG=false
```

## Extending

### Add Custom Filter

```python
from news_scanner.pipeline.filters import FilterPipeline

pipeline = FilterPipeline()
pipeline.add_category_filter(["finance"])
pipeline.add_topic_filter(["CRYPTO"])
pipeline.add_keyword_filter(["bitcoin", "ethereum"])
pipeline.add_age_filter(hours=24)

# Custom filter function
pipeline.add_filter(lambda item: len(item.title) > 20)

filtered = pipeline.apply(items)
```

### Add Custom Storage

```python
from news_scanner.storage import BaseStorage

class RedisStorage(BaseStorage):
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)

    async def save(self, items):
        for item in items:
            await self.redis.set(f"news:{item.id}", item.to_json())

    async def load(self):
        # ...

    async def clear(self):
        # ...
```

### Add ML-Based Sentiment

```python
from transformers import pipeline as hf_pipeline
from news_scanner.analytics import SentimentAnalyzer
from news_scanner.analytics.sentiment import SentimentResult, Sentiment

class TransformerSentiment(SentimentAnalyzer):
    def __init__(self):
        self.model = hf_pipeline("sentiment-analysis")

    def analyze(self, text: str) -> SentimentResult:
        result = self.model(text[:512])[0]
        score = result["score"] if result["label"] == "POSITIVE" else -result["score"]

        return SentimentResult(
            sentiment=Sentiment.POSITIVE if score > 0 else Sentiment.NEGATIVE,
            score=score,
            confidence=result["score"],
            positive_keywords=[],
            negative_keywords=[]
        )
```

## License

MIT
