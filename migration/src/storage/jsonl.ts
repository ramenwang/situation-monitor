/**
 * JSONL Storage Adapter
 *
 * Stores news items as newline-delimited JSON.
 * Each line is a complete JSON object.
 */

import * as fs from 'fs';
import * as path from 'path';
import type { NormalizedNewsItem, StorageAdapter } from '../types';
import { logger } from '../utils';

export interface JsonlStorageOptions {
  /** Output file path */
  filePath: string;
  /** Append to existing file (default: false, overwrites) */
  append?: boolean;
  /** Pretty print JSON (default: false) */
  pretty?: boolean;
}

/**
 * JSONL Storage Adapter
 */
export class JsonlStorage implements StorageAdapter {
  private filePath: string;
  private append: boolean;
  private pretty: boolean;

  constructor(options: JsonlStorageOptions) {
    this.filePath = options.filePath;
    this.append = options.append ?? false;
    this.pretty = options.pretty ?? false;

    // Ensure output directory exists
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  async save(items: NormalizedNewsItem[]): Promise<void> {
    const lines = items.map((item) =>
      this.pretty ? JSON.stringify(item, null, 2) : JSON.stringify(item)
    );

    const content = lines.join('\n') + '\n';

    if (this.append) {
      fs.appendFileSync(this.filePath, content, 'utf8');
    } else {
      fs.writeFileSync(this.filePath, content, 'utf8');
    }

    logger.info(`JSONL: Saved ${items.length} items to ${this.filePath}`);
  }

  async load(): Promise<NormalizedNewsItem[]> {
    if (!fs.existsSync(this.filePath)) {
      return [];
    }

    const content = fs.readFileSync(this.filePath, 'utf8');
    const lines = content.trim().split('\n').filter(Boolean);

    const items: NormalizedNewsItem[] = [];

    for (const line of lines) {
      try {
        const item = JSON.parse(line) as NormalizedNewsItem;
        items.push(item);
      } catch (error) {
        logger.warn('JSONL: Failed to parse line:', line.slice(0, 50));
      }
    }

    logger.info(`JSONL: Loaded ${items.length} items from ${this.filePath}`);
    return items;
  }

  async clear(): Promise<void> {
    if (fs.existsSync(this.filePath)) {
      fs.unlinkSync(this.filePath);
      logger.info(`JSONL: Cleared ${this.filePath}`);
    }
  }

  /**
   * Get the output file path
   */
  getFilePath(): string {
    return this.filePath;
  }
}

/**
 * Create a JSONL storage adapter with default output path
 */
export function createJsonlStorage(outputDir = './output'): JsonlStorage {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const filePath = path.join(outputDir, `news-${timestamp}.jsonl`);

  return new JsonlStorage({ filePath });
}
