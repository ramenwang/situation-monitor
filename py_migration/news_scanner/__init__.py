"""
Trading News Scanner

A modular news scanning and summarization toolkit for trading applications.
"""

__version__ = "1.0.0"

from .models import NormalizedNewsItem, PipelineResult
from .pipeline import NewsPipeline, run_pipeline
from .connectors import GdeltConnector, RSSConnector
from .analytics import TopicDetector, AlertDetector, TickerExtractor, Deduplicator
from .storage import JsonlStorage, SqliteStorage

__all__ = [
    "NormalizedNewsItem",
    "PipelineResult",
    "NewsPipeline",
    "run_pipeline",
    "GdeltConnector",
    "RSSConnector",
    "TopicDetector",
    "AlertDetector",
    "TickerExtractor",
    "Deduplicator",
    "JsonlStorage",
    "SqliteStorage",
]
