"""
Base storage interface.
"""

from abc import ABC, abstractmethod

from ..models import NormalizedNewsItem


class BaseStorage(ABC):
    """
    Abstract base class for storage adapters.
    """

    @abstractmethod
    async def save(self, items: list[NormalizedNewsItem]) -> None:
        """Save news items."""
        pass

    @abstractmethod
    async def load(self) -> list[NormalizedNewsItem]:
        """Load all news items."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored items."""
        pass

    def get_path(self) -> str:
        """Get storage path/location."""
        return ""
