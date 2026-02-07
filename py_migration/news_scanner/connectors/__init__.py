"""
News source connectors.

Each connector fetches data from an external source and returns normalized items.
"""

from .gdelt import GdeltConnector
from .rss import RSSConnector
from .base import BaseConnector

__all__ = [
    "BaseConnector",
    "GdeltConnector",
    "RSSConnector",
]
