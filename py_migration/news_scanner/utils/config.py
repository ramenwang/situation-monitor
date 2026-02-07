"""
Configuration for the news scanner.

All configuration is loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from ..models import FeedSource, IntelSource


@dataclass
class Config:
    """Main configuration object."""

    # Debug mode
    debug: bool = False

    # API Keys
    finnhub_api_key: str = ""
    fred_api_key: str = ""

    # CORS Proxies (for RSS feeds)
    cors_proxies: list[str] = field(default_factory=lambda: [
        "https://api.allorigins.win/raw?url=",
        "https://corsproxy.io/?url=",
    ])

    # API Base URLs
    gdelt_base_url: str = "https://api.gdeltproject.org"
    finnhub_base_url: str = "https://finnhub.io/api/v1"
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    # Request settings
    request_timeout: int = 15
    delay_between_requests: float = 0.5

    # Cache settings (seconds)
    cache_ttl_news: int = 300
    cache_ttl_markets: int = 60

    # Output settings
    output_dir: str = "./output"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
            fred_api_key=os.getenv("FRED_API_KEY", ""),
            cors_proxies=[
                p for p in [
                    os.getenv("CORS_PROXY_PRIMARY", "https://api.allorigins.win/raw?url="),
                    os.getenv("CORS_PROXY_FALLBACK", "https://corsproxy.io/?url="),
                ] if p
            ],
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "15")),
            delay_between_requests=float(os.getenv("DELAY_BETWEEN_REQUESTS", "0.5")),
            cache_ttl_news=int(os.getenv("CACHE_TTL_NEWS", "300")),
            cache_ttl_markets=int(os.getenv("CACHE_TTL_MARKETS", "60")),
            output_dir=os.getenv("OUTPUT_DIR", "./output"),
        )


# Global config instance
config = Config.from_env()


# =============================================================================
# Feed Sources
# =============================================================================

FEEDS: dict[str, list[FeedSource]] = {
    "politics": [
        FeedSource("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "politics"),
        FeedSource("NPR News", "https://feeds.npr.org/1001/rss.xml", "politics"),
        FeedSource("Guardian World", "https://www.theguardian.com/world/rss", "politics"),
        FeedSource("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "politics"),
    ],
    "tech": [
        FeedSource("Hacker News", "https://hnrss.org/frontpage", "tech"),
        FeedSource("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab", "tech"),
        FeedSource("The Verge", "https://www.theverge.com/rss/index.xml", "tech"),
        FeedSource("MIT Tech Review", "https://www.technologyreview.com/feed/", "tech"),
    ],
    "finance": [
        FeedSource("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "finance"),
        FeedSource("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories", "finance"),
        FeedSource("Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "finance"),
        FeedSource("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml", "finance"),
    ],
    "gov": [
        FeedSource("White House", "https://www.whitehouse.gov/news/feed/", "gov"),
        FeedSource("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "gov"),
        FeedSource("SEC Announcements", "https://www.sec.gov/news/pressreleases.rss", "gov"),
    ],
    "ai": [
        FeedSource("OpenAI Blog", "https://openai.com/news/rss.xml", "ai"),
        FeedSource("ArXiv AI", "https://rss.arxiv.org/rss/cs.AI", "ai"),
    ],
    "intel": [
        FeedSource("CSIS", "https://www.csis.org/analysis/feed", "intel"),
        FeedSource("Brookings", "https://www.brookings.edu/feed/", "intel"),
    ],
}

INTEL_SOURCES: list[IntelSource] = [
    IntelSource("CSIS", "https://www.csis.org/analysis/feed", "intel", "think-tank", ["defense", "geopolitics"]),
    IntelSource("Brookings", "https://www.brookings.edu/feed/", "intel", "think-tank", ["policy", "geopolitics"]),
    IntelSource("CFR", "https://www.cfr.org/rss.xml", "intel", "think-tank", ["foreign-policy"]),
    IntelSource("Defense One", "https://www.defenseone.com/rss/all/", "intel", "defense", ["military", "defense"]),
    IntelSource("War on Rocks", "https://warontherocks.com/feed/", "intel", "defense", ["military", "strategy"]),
    IntelSource("Breaking Defense", "https://breakingdefense.com/feed/", "intel", "defense", ["military", "defense"]),
    IntelSource("The Diplomat", "https://thediplomat.com/feed/", "intel", "regional", ["asia-pacific"], "APAC"),
    IntelSource("Al-Monitor", "https://www.al-monitor.com/rss", "intel", "regional", ["middle-east"], "MENA"),
    IntelSource("Bellingcat", "https://www.bellingcat.com/feed/", "intel", "osint", ["investigation", "osint"]),
    IntelSource("CISA Alerts", "https://www.cisa.gov/uscert/ncas/alerts.xml", "intel", "cyber", ["cyber", "security"]),
    IntelSource("Krebs Security", "https://krebsonsecurity.com/feed/", "intel", "cyber", ["cyber", "security"]),
]

# GDELT query templates by category
GDELT_QUERIES: dict[str, str] = {
    "politics": "(politics OR government OR election OR congress)",
    "tech": "(technology OR software OR startup OR AI)",
    "finance": '(finance OR "stock market" OR economy OR banking)',
    "gov": '("federal government" OR "white house" OR congress OR regulation)',
    "ai": '("artificial intelligence" OR "machine learning" OR AI OR ChatGPT)',
    "intel": "(intelligence OR security OR military OR defense)",
}
