"""
JSONL Storage Adapter

Stores news items as newline-delimited JSON.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from .base import BaseStorage
from ..models import NormalizedNewsItem
from ..utils import logger


class JsonlStorage(BaseStorage):
    """
    JSONL file storage.

    Example usage:
        storage = JsonlStorage("output/news.jsonl")
        await storage.save(items)
        items = await storage.load()

        # Auto-generated filename:
        storage = JsonlStorage.with_timestamp("output")
    """

    def __init__(self, file_path: str, append: bool = False):
        """
        Initialize JSONL storage.

        Args:
            file_path: Path to JSONL file.
            append: Whether to append to existing file.
        """
        self.file_path = file_path
        self.append = append

        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def with_timestamp(cls, output_dir: str = "./output") -> "JsonlStorage":
        """Create storage with timestamped filename."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        file_path = os.path.join(output_dir, f"news-{timestamp}.jsonl")
        return cls(file_path)

    async def save(self, items: list[NormalizedNewsItem]) -> None:
        """Save news items to JSONL file."""
        mode = "a" if self.append else "w"

        with open(self.file_path, mode, encoding="utf-8") as f:
            for item in items:
                line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(line + "\n")

        logger.info(f"JSONL: Saved {len(items)} items to {self.file_path}")

    async def load(self) -> list[NormalizedNewsItem]:
        """Load news items from JSONL file."""
        if not os.path.exists(self.file_path):
            return []

        items = []

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    items.append(NormalizedNewsItem.from_dict(data))
                except json.JSONDecodeError as e:
                    logger.warning(f"JSONL: Failed to parse line: {e}")

        logger.info(f"JSONL: Loaded {len(items)} items from {self.file_path}")
        return items

    async def clear(self) -> None:
        """Clear the JSONL file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            logger.info(f"JSONL: Cleared {self.file_path}")

    def get_path(self) -> str:
        """Get file path."""
        return self.file_path

    # Sync versions for convenience
    def save_sync(self, items: list[NormalizedNewsItem]) -> None:
        """Synchronous save."""
        import asyncio
        asyncio.get_event_loop().run_until_complete(self.save(items))

    def load_sync(self) -> list[NormalizedNewsItem]:
        """Synchronous load."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.load())
