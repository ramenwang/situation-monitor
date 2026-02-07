"""
SQLite Storage Adapter

Stores news items in a SQLite database.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Optional

from .base import BaseStorage
from ..models import NormalizedNewsItem, NewsMetadata
from ..utils import logger


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    authors TEXT,
    summary TEXT,
    content_text TEXT,
    tickers TEXT,
    topics TEXT,
    language TEXT DEFAULT 'en',
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_INDICES_SQL = """
CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at);
CREATE INDEX IF NOT EXISTS idx_source ON news_items(source);
CREATE INDEX IF NOT EXISTS idx_created_at ON news_items(created_at);
"""


class SqliteStorage(BaseStorage):
    """
    SQLite database storage.

    Example usage:
        storage = SqliteStorage("output/news.db")
        await storage.save(items)
        items = await storage.load()

        # Query with SQL:
        items = storage.query("source = ?", ["BBC World"])
        count = storage.count()
    """

    def __init__(self, db_path: str):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = self._get_conn()
        conn.executescript(CREATE_TABLE_SQL + CREATE_INDICES_SQL)
        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    async def save(self, items: list[NormalizedNewsItem]) -> None:
        """Save news items to database."""
        conn = self._get_conn()

        insert_sql = """
        INSERT OR REPLACE INTO news_items
        (id, source, url, title, published_at, fetched_at, authors, summary,
         content_text, tickers, topics, language, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for item in items:
            conn.execute(insert_sql, (
                item.id,
                item.source,
                item.url,
                item.title,
                item.published_at,
                item.fetched_at,
                json.dumps(item.authors),
                item.summary,
                item.content_text,
                json.dumps(item.tickers),
                json.dumps(item.topics),
                item.language,
                json.dumps(item.metadata.to_dict() if item.metadata else {}),
            ))

        conn.commit()
        logger.info(f"SQLite: Saved {len(items)} items to {self.db_path}")

    async def load(self) -> list[NormalizedNewsItem]:
        """Load all news items from database."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM news_items ORDER BY published_at DESC"
        )

        items = []
        for row in cursor:
            items.append(self._row_to_item(row))

        logger.info(f"SQLite: Loaded {len(items)} items from {self.db_path}")
        return items

    async def clear(self) -> None:
        """Clear all items from database."""
        conn = self._get_conn()
        conn.execute("DELETE FROM news_items")
        conn.commit()
        logger.info(f"SQLite: Cleared {self.db_path}")

    def query(
        self,
        where_clause: str,
        params: Optional[list] = None,
        limit: Optional[int] = None
    ) -> list[NormalizedNewsItem]:
        """
        Query items with SQL WHERE clause.

        Args:
            where_clause: SQL WHERE clause (without "WHERE").
            params: Query parameters.
            limit: Max items to return.

        Returns:
            List of matching items.
        """
        conn = self._get_conn()

        sql = f"SELECT * FROM news_items WHERE {where_clause} ORDER BY published_at DESC"
        if limit:
            sql += f" LIMIT {limit}"

        cursor = conn.execute(sql, params or [])
        return [self._row_to_item(row) for row in cursor]

    def count(self) -> int:
        """Get count of items in database."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT COUNT(*) FROM news_items")
        return cursor.fetchone()[0]

    def get_sources(self) -> list[str]:
        """Get list of unique sources."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT DISTINCT source FROM news_items ORDER BY source")
        return [row[0] for row in cursor]

    def get_by_source(self, source: str, limit: int = 100) -> list[NormalizedNewsItem]:
        """Get items by source."""
        return self.query("source = ?", [source], limit)

    def get_alerts(self, limit: int = 100) -> list[NormalizedNewsItem]:
        """Get alert items."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM news_items
            WHERE json_extract(metadata, '$.is_alert') = 1
            ORDER BY published_at DESC
            LIMIT ?
        """, [limit])
        return [self._row_to_item(row) for row in cursor]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_path(self) -> str:
        """Get database path."""
        return self.db_path

    def _row_to_item(self, row: sqlite3.Row) -> NormalizedNewsItem:
        """Convert database row to NormalizedNewsItem."""
        metadata_dict = json.loads(row["metadata"] or "{}")

        return NormalizedNewsItem(
            id=row["id"],
            source=row["source"],
            url=row["url"],
            title=row["title"],
            published_at=row["published_at"],
            fetched_at=row["fetched_at"],
            authors=json.loads(row["authors"] or "[]"),
            summary=row["summary"] or "",
            content_text=row["content_text"] or "",
            tickers=json.loads(row["tickers"] or "[]"),
            topics=json.loads(row["topics"] or "[]"),
            language=row["language"] or "en",
            metadata=NewsMetadata(**metadata_dict),
        )
