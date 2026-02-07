/**
 * SQLite Storage Adapter
 *
 * Stores news items in a SQLite database.
 * Uses better-sqlite3 for synchronous API.
 *
 * NOTE: Requires `better-sqlite3` package:
 *   npm install better-sqlite3
 *   npm install -D @types/better-sqlite3
 */

import * as fs from 'fs';
import * as path from 'path';
import type { NormalizedNewsItem, StorageAdapter } from '../types';
import { logger } from '../utils';

// Type for better-sqlite3 (optional dependency)
interface Database {
  prepare(sql: string): Statement;
  exec(sql: string): void;
  close(): void;
}

interface Statement {
  run(...params: unknown[]): void;
  get(...params: unknown[]): unknown;
  all(...params: unknown[]): unknown[];
}

export interface SqliteStorageOptions {
  /** Database file path */
  filePath: string;
  /** Table name (default: 'news_items') */
  tableName?: string;
}

const CREATE_TABLE_SQL = `
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
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`;

const CREATE_INDEX_SQL = `
  CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at);
  CREATE INDEX IF NOT EXISTS idx_source ON news_items(source);
`;

/**
 * SQLite Storage Adapter
 */
export class SqliteStorage implements StorageAdapter {
  private filePath: string;
  private tableName: string;
  private db: Database | null = null;

  constructor(options: SqliteStorageOptions) {
    this.filePath = options.filePath;
    this.tableName = options.tableName ?? 'news_items';

    // Ensure output directory exists
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private async getDb(): Promise<Database> {
    if (this.db) return this.db;

    try {
      // Dynamic import for optional dependency
      const BetterSqlite3 = await import('better-sqlite3');
      const Database = BetterSqlite3.default || BetterSqlite3;
      this.db = new Database(this.filePath) as Database;

      // Create table if not exists
      this.db.exec(CREATE_TABLE_SQL);
      this.db.exec(CREATE_INDEX_SQL);

      return this.db;
    } catch (error) {
      throw new Error(
        `SQLite storage requires 'better-sqlite3' package. Install with: npm install better-sqlite3\n` +
        `Original error: ${(error as Error).message}`
      );
    }
  }

  async save(items: NormalizedNewsItem[]): Promise<void> {
    const db = await this.getDb();

    const insertSql = `
      INSERT OR REPLACE INTO news_items
      (id, source, url, title, published_at, fetched_at, authors, summary, content_text, tickers, topics, language, metadata)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const stmt = db.prepare(insertSql);

    for (const item of items) {
      stmt.run(
        item.id,
        item.source,
        item.url,
        item.title,
        item.published_at,
        item.fetched_at,
        JSON.stringify(item.authors),
        item.summary,
        item.content_text,
        JSON.stringify(item.tickers),
        JSON.stringify(item.topics),
        item.language,
        JSON.stringify(item.metadata)
      );
    }

    logger.info(`SQLite: Saved ${items.length} items to ${this.filePath}`);
  }

  async load(): Promise<NormalizedNewsItem[]> {
    const db = await this.getDb();

    const rows = db.prepare(`SELECT * FROM news_items ORDER BY published_at DESC`).all() as Array<{
      id: string;
      source: string;
      url: string;
      title: string;
      published_at: string;
      fetched_at: string;
      authors: string;
      summary: string;
      content_text: string;
      tickers: string;
      topics: string;
      language: string;
      metadata: string;
    }>;

    const items: NormalizedNewsItem[] = rows.map((row) => ({
      id: row.id,
      source: row.source,
      url: row.url,
      title: row.title,
      published_at: row.published_at,
      fetched_at: row.fetched_at,
      authors: JSON.parse(row.authors || '[]'),
      summary: row.summary || '',
      content_text: row.content_text || '',
      tickers: JSON.parse(row.tickers || '[]'),
      topics: JSON.parse(row.topics || '[]'),
      language: row.language || 'en',
      metadata: JSON.parse(row.metadata || '{}'),
    }));

    logger.info(`SQLite: Loaded ${items.length} items from ${this.filePath}`);
    return items;
  }

  async clear(): Promise<void> {
    const db = await this.getDb();
    db.exec(`DELETE FROM news_items`);
    logger.info(`SQLite: Cleared all items from ${this.filePath}`);
  }

  /**
   * Query items with SQL WHERE clause
   */
  async query(whereClause: string, params: unknown[] = []): Promise<NormalizedNewsItem[]> {
    const db = await this.getDb();
    const sql = `SELECT * FROM news_items WHERE ${whereClause} ORDER BY published_at DESC`;
    const rows = db.prepare(sql).all(...params) as Array<Record<string, unknown>>;

    return rows.map((row) => ({
      id: row.id as string,
      source: row.source as string,
      url: row.url as string,
      title: row.title as string,
      published_at: row.published_at as string,
      fetched_at: row.fetched_at as string,
      authors: JSON.parse((row.authors as string) || '[]'),
      summary: (row.summary as string) || '',
      content_text: (row.content_text as string) || '',
      tickers: JSON.parse((row.tickers as string) || '[]'),
      topics: JSON.parse((row.topics as string) || '[]'),
      language: (row.language as string) || 'en',
      metadata: JSON.parse((row.metadata as string) || '{}'),
    }));
  }

  /**
   * Get count of items
   */
  async count(): Promise<number> {
    const db = await this.getDb();
    const result = db.prepare(`SELECT COUNT(*) as count FROM news_items`).get() as { count: number };
    return result.count;
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  /**
   * Get the database file path
   */
  getFilePath(): string {
    return this.filePath;
  }
}

/**
 * Create a SQLite storage adapter with default output path
 */
export function createSqliteStorage(outputDir = './output'): SqliteStorage {
  const filePath = path.join(outputDir, 'news.db');
  return new SqliteStorage({ filePath });
}
