"""
Storage adapters for persisting news items.
"""

from .base import BaseStorage
from .jsonl import JsonlStorage
from .sqlite import SqliteStorage

__all__ = [
    "BaseStorage",
    "JsonlStorage",
    "SqliteStorage",
]
