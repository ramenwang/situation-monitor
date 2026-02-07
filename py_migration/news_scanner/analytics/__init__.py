"""
Analytics modules for news processing.

Each analyzer is independent and can be used standalone or composed in a pipeline.
"""

from .topics import TopicDetector
from .alerts import AlertDetector
from .tickers import TickerExtractor
from .regions import RegionDetector
from .dedup import Deduplicator
from .sentiment import SentimentAnalyzer

__all__ = [
    "TopicDetector",
    "AlertDetector",
    "TickerExtractor",
    "RegionDetector",
    "Deduplicator",
    "SentimentAnalyzer",
]
