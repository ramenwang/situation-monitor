"""
News Pipeline Runner

Orchestrates: Fetch -> Parse -> Filter -> Deduplicate -> Store
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from ..models import NormalizedNewsItem, PipelineResult, PipelineStats, PipelineError
from ..connectors import GdeltConnector, RSSConnector
from ..parsers import Normalizer
from ..analytics import Deduplicator
from ..storage import BaseStorage, JsonlStorage
from ..utils import logger, now_iso
from .filters import FilterConfig, filter_items


@dataclass
class PipelineOptions:
    """Pipeline configuration options."""
    # Sources
    use_gdelt: bool = True
    use_rss: bool = True
    use_intel: bool = True
    categories: list[str] = field(default_factory=lambda: [
        "finance", "tech", "politics", "gov", "ai", "intel"
    ])

    # Filters
    filter_config: Optional[FilterConfig] = None

    # Storage
    storage: Optional[BaseStorage] = None
    output_dir: str = "./output"

    # Processing
    normalize: bool = True
    deduplicate: bool = True


class NewsPipeline:
    """
    Main news pipeline.

    Example usage:
        # Simple usage
        pipeline = NewsPipeline()
        result = await pipeline.run()

        # With configuration
        pipeline = NewsPipeline(PipelineOptions(
            categories=["finance", "tech"],
            use_intel=False,
            filter_config=FilterConfig(max_age_hours=24)
        ))
        result = await pipeline.run()

        # With custom storage
        pipeline = NewsPipeline(PipelineOptions(
            storage=SqliteStorage("output/news.db")
        ))
    """

    def __init__(self, options: Optional[PipelineOptions] = None):
        """
        Initialize pipeline.

        Args:
            options: Pipeline configuration options.
        """
        self.options = options or PipelineOptions()

        # Initialize components
        self.gdelt = GdeltConnector()
        self.rss = RSSConnector()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()

    async def run(self) -> PipelineResult:
        """
        Run the full pipeline.

        Returns:
            PipelineResult with items, stats, and errors.
        """
        start_time = time.time()
        errors: list[PipelineError] = []
        all_items: list[NormalizedNewsItem] = []

        # Stage 1: Fetch
        logger.info("Pipeline: Starting fetch stage")

        if self.options.use_gdelt:
            try:
                items = await self.gdelt.fetch(categories=self.options.categories)
                all_items.extend(items)
                logger.info(f"Pipeline: GDELT fetched {len(items)} items")
            except Exception as e:
                errors.append(PipelineError(
                    stage="fetch",
                    source="GDELT",
                    message=str(e),
                    timestamp=now_iso()
                ))

        if self.options.use_rss:
            try:
                items = await self.rss.fetch(categories=self.options.categories)
                all_items.extend(items)
                logger.info(f"Pipeline: RSS fetched {len(items)} items")
            except Exception as e:
                errors.append(PipelineError(
                    stage="fetch",
                    source="RSS",
                    message=str(e),
                    timestamp=now_iso()
                ))

        if self.options.use_intel:
            try:
                items = await self.rss.fetch_intel()
                all_items.extend(items)
                logger.info(f"Pipeline: Intel fetched {len(items)} items")
            except Exception as e:
                errors.append(PipelineError(
                    stage="fetch",
                    source="Intel",
                    message=str(e),
                    timestamp=now_iso()
                ))

        fetched_count = len(all_items)

        # Stage 2: Normalize
        if self.options.normalize:
            logger.info("Pipeline: Starting normalize stage")
            try:
                all_items = self.normalizer.normalize_many(all_items)
            except Exception as e:
                errors.append(PipelineError(
                    stage="parse",
                    source=None,
                    message=str(e),
                    timestamp=now_iso()
                ))

        parsed_count = len(all_items)

        # Stage 3: Filter
        filtered_count = 0
        if self.options.filter_config:
            logger.info("Pipeline: Starting filter stage")
            before = len(all_items)
            all_items = filter_items(all_items, self.options.filter_config)
            filtered_count = before - len(all_items)
            logger.info(f"Pipeline: Filtered {filtered_count} items")

        # Stage 4: Deduplicate
        dedup_count = 0
        if self.options.deduplicate:
            logger.info("Pipeline: Starting dedup stage")
            result = self.deduplicator.deduplicate(all_items)
            all_items = result.items
            dedup_count = result.removed_count
            logger.info(f"Pipeline: Deduplicated {dedup_count} items")

        # Sort by date (newest first)
        all_items.sort(
            key=lambda x: x.published_at,
            reverse=True
        )

        # Stage 5: Store
        stored_count = len(all_items)
        storage = self.options.storage
        if storage is None and self.options.output_dir:
            storage = JsonlStorage.with_timestamp(self.options.output_dir)

        if storage:
            logger.info("Pipeline: Starting store stage")
            try:
                await storage.save(all_items)
                logger.info(f"Pipeline: Stored {stored_count} items")
            except Exception as e:
                errors.append(PipelineError(
                    stage="store",
                    source=None,
                    message=str(e),
                    timestamp=now_iso()
                ))

        duration_ms = int((time.time() - start_time) * 1000)

        stats = PipelineStats(
            fetched=fetched_count,
            parsed=parsed_count,
            filtered=filtered_count,
            deduplicated=dedup_count,
            stored=stored_count,
            duration_ms=duration_ms
        )

        logger.info(f"Pipeline: Complete in {duration_ms}ms ({len(all_items)} items)")

        return PipelineResult(
            items=all_items,
            stats=stats,
            errors=errors
        )

    def set_filter(self, config: FilterConfig) -> "NewsPipeline":
        """Set filter configuration."""
        self.options.filter_config = config
        return self

    def set_storage(self, storage: BaseStorage) -> "NewsPipeline":
        """Set storage adapter."""
        self.options.storage = storage
        return self

    def set_categories(self, categories: list[str]) -> "NewsPipeline":
        """Set categories to fetch."""
        self.options.categories = categories
        return self


async def run_pipeline(options: Optional[PipelineOptions] = None) -> PipelineResult:
    """
    Run the news pipeline.

    Convenience function for simple usage:
        result = await run_pipeline()

    With options:
        result = await run_pipeline(PipelineOptions(
            categories=["finance"],
            use_intel=False
        ))
    """
    pipeline = NewsPipeline(options)
    return await pipeline.run()
