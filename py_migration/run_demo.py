#!/usr/bin/env python3
"""
News Pipeline Demo

Demonstrates the full pipeline:
1. Fetches news from GDELT and RSS sources
2. Parses and normalizes articles
3. Filters and deduplicates
4. Outputs to JSONL file

Usage:
    python run_demo.py
    python run_demo.py --categories finance tech
    python run_demo.py --alerts-only
"""

import asyncio
import argparse
from collections import Counter

from news_scanner import (
    NewsPipeline,
    PipelineResult,
    JsonlStorage,
)
from news_scanner.pipeline import PipelineOptions, FilterConfig
from news_scanner.utils import logger


def print_results(result: PipelineResult, storage_path: str):
    """Print pipeline results."""
    print()
    print("=" * 60)
    print("Pipeline Results")
    print("=" * 60)
    print()
    print(f"Fetched:      {result.stats.fetched} items")
    print(f"Parsed:       {result.stats.parsed} items")
    print(f"Filtered:     {result.stats.filtered} items removed")
    print(f"Deduplicated: {result.stats.deduplicated} duplicates removed")
    print(f"Stored:       {result.stats.stored} items")
    print(f"Duration:     {result.stats.duration_ms}ms")
    print()

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - [{error.stage}] {error.source or ''}: {error.message}")
        print()

    # Sample items
    print("Sample Items (first 5):")
    print("-" * 60)

    for item in result.items[:5]:
        print()
        title = item.title[:70] + "..." if len(item.title) > 70 else item.title
        print(f"Title:     {title}")
        print(f"Source:    {item.source}")
        print(f"Published: {item.published_at}")
        print(f"Topics:    {', '.join(item.topics) or 'none'}")
        print(f"Tickers:   {', '.join(item.tickers) or 'none'}")
        alert_str = f"YES ({item.metadata.alert_keyword})" if item.metadata.is_alert else "no"
        print(f"Alert:     {alert_str}")

    print()
    print("-" * 60)
    print(f"Output saved to: {storage_path}")
    print()

    # Alerts
    alerts = [item for item in result.items if item.metadata.is_alert]
    if alerts:
        print("=" * 60)
        print(f"ALERTS ({len(alerts)} items)")
        print("=" * 60)
        for alert in alerts[:10]:
            kw = alert.metadata.alert_keyword.upper() if alert.metadata.alert_keyword else "?"
            print(f"[{kw}] {alert.title[:55]}...")
        if len(alerts) > 10:
            print(f"... and {len(alerts) - 10} more alerts")
        print()

    # Topic distribution
    topic_counts = Counter()
    for item in result.items:
        for topic in item.topics:
            topic_counts[topic] += 1

    if topic_counts:
        print("Topic Distribution:")
        for topic, count in topic_counts.most_common():
            bar = "#" * min(count, 30)
            print(f"  {topic:<12} {count:>3} {bar}")
        print()

    # Source distribution
    source_counts = Counter(item.source for item in result.items)
    print("Source Distribution (top 10):")
    for source, count in source_counts.most_common(10):
        print(f"  {source:<25} {count}")
    print()


async def main():
    parser = argparse.ArgumentParser(description="News Pipeline Demo")
    parser.add_argument(
        "--categories",
        nargs="+",
        default=["finance", "tech", "politics"],
        help="Categories to fetch"
    )
    parser.add_argument(
        "--no-gdelt",
        action="store_true",
        help="Skip GDELT source"
    )
    parser.add_argument(
        "--no-rss",
        action="store_true",
        help="Skip RSS sources"
    )
    parser.add_argument(
        "--no-intel",
        action="store_true",
        help="Skip intel sources"
    )
    parser.add_argument(
        "--alerts-only",
        action="store_true",
        help="Only show alert items"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        help="Max age in hours"
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logger.enable_debug()

    print("=" * 60)
    print("Trading News Scanner - Demo")
    print("=" * 60)
    print()
    print(f"Categories: {', '.join(args.categories)}")
    print(f"Sources: GDELT={not args.no_gdelt}, RSS={not args.no_rss}, Intel={not args.no_intel}")
    print()

    # Build filter config
    filter_config = None
    if args.alerts_only or args.max_age:
        filter_config = FilterConfig(
            alerts_only=args.alerts_only,
            max_age_hours=args.max_age
        )

    # Create storage
    storage = JsonlStorage.with_timestamp(args.output)

    # Create pipeline
    options = PipelineOptions(
        use_gdelt=not args.no_gdelt,
        use_rss=not args.no_rss,
        use_intel=not args.no_intel,
        categories=args.categories,
        filter_config=filter_config,
        storage=storage
    )

    pipeline = NewsPipeline(options)

    print("Starting pipeline...")
    result = await pipeline.run()

    print_results(result, storage.get_path())
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
