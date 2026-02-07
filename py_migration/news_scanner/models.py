"""
Data models for the news scanner.

Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


class NewsCategory(str, Enum):
    """News category types."""
    POLITICS = "politics"
    TECH = "tech"
    FINANCE = "finance"
    GOV = "gov"
    AI = "ai"
    INTEL = "intel"
    GENERAL = "general"


@dataclass
class NewsMetadata:
    """Extended metadata for news items."""
    category: Optional[str] = None
    is_alert: bool = False
    alert_keyword: Optional[str] = None
    region: Optional[str] = None
    domain: Optional[str] = None
    image_url: Optional[str] = None
    raw: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values and raw."""
        return {k: v for k, v in asdict(self).items()
                if v is not None and k != 'raw'}


@dataclass
class NormalizedNewsItem:
    """
    Normalized news item schema.

    All news items from any source are transformed to this schema.
    """
    id: str
    source: str
    url: str
    title: str
    published_at: str  # ISO8601
    fetched_at: str    # ISO8601
    authors: list[str] = field(default_factory=list)
    summary: str = ""
    content_text: str = ""
    tickers: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    language: str = "en"
    metadata: NewsMetadata = field(default_factory=NewsMetadata)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert metadata to dict
        if isinstance(self.metadata, NewsMetadata):
            data['metadata'] = self.metadata.to_dict()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "NormalizedNewsItem":
        """Create from dictionary."""
        metadata_data = data.pop('metadata', {})
        if isinstance(metadata_data, dict):
            metadata = NewsMetadata(**metadata_data)
        else:
            metadata = metadata_data
        return cls(**data, metadata=metadata)


@dataclass
class PipelineError:
    """Error that occurred during pipeline execution."""
    stage: str  # 'fetch', 'parse', 'filter', 'dedup', 'store'
    source: Optional[str]
    message: str
    timestamp: str


@dataclass
class PipelineStats:
    """Statistics from pipeline execution."""
    fetched: int = 0
    parsed: int = 0
    filtered: int = 0
    deduplicated: int = 0
    stored: int = 0
    duration_ms: int = 0


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    items: list[NormalizedNewsItem]
    stats: PipelineStats
    errors: list[PipelineError]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'items': [item.to_dict() for item in self.items],
            'stats': asdict(self.stats),
            'errors': [asdict(e) for e in self.errors],
        }


@dataclass
class FeedSource:
    """RSS feed source configuration."""
    name: str
    url: str
    category: str = "general"


@dataclass
class IntelSource(FeedSource):
    """Intel source with additional metadata."""
    source_type: str = "general"  # 'think-tank', 'defense', 'osint', 'cyber'
    topics: list[str] = field(default_factory=list)
    region: Optional[str] = None
