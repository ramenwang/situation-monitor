"""
Base connector interface.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import NormalizedNewsItem


class BaseConnector(ABC):
    """
    Abstract base class for news connectors.

    All connectors should implement this interface.
    """

    @abstractmethod
    async def fetch(self, **kwargs) -> list[NormalizedNewsItem]:
        """
        Fetch news items from the source.

        Returns:
            List of normalized news items.
        """
        pass

    @abstractmethod
    async def fetch_category(self, category: str, **kwargs) -> list[NormalizedNewsItem]:
        """
        Fetch news items for a specific category.

        Args:
            category: News category to fetch.

        Returns:
            List of normalized news items.
        """
        pass

    def get_name(self) -> str:
        """Get connector name."""
        return self.__class__.__name__
