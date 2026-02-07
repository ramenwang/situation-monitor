/**
 * News Pipeline
 *
 * Orchestrates: Fetch -> Parse -> Filter -> Deduplicate -> Store
 */

import type { NormalizedNewsItem, PipelineResult, PipelineError, FilterConfig, StorageAdapter, NewsCategory } from '../types';
import { GdeltConnector, RSSConnector } from '../connectors';
import { normalizeItem } from '../parsers';
import { logger, hashCode } from '../utils';

export interface PipelineOptions {
  /** Categories to fetch */
  categories?: NewsCategory[];
  /** Include GDELT as a source */
  useGdelt?: boolean;
  /** Include RSS feeds as sources */
  useRss?: boolean;
  /** Include intel sources (think tanks, etc.) */
  useIntel?: boolean;
  /** Filter configuration */
  filter?: FilterConfig;
  /** Storage adapter for output */
  storage?: StorageAdapter;
  /** CORS proxies for RSS */
  corsProxies?: string[];
}

const DEFAULT_OPTIONS: Required<Omit<PipelineOptions, 'storage'>> & { storage?: StorageAdapter } = {
  categories: ['politics', 'tech', 'finance', 'gov', 'ai', 'intel'],
  useGdelt: true,
  useRss: true,
  useIntel: true,
  filter: {},
  storage: undefined,
  corsProxies: [],
};

/**
 * Filter items based on configuration
 */
export function filterItems(items: NormalizedNewsItem[], config: FilterConfig): NormalizedNewsItem[] {
  return items.filter((item) => {
    // Category filter
    if (config.categories?.length && item.metadata?.category) {
      if (!config.categories.includes(item.metadata.category)) {
        return false;
      }
    }

    // Region filter
    if (config.regions?.length && item.metadata?.region) {
      if (!config.regions.includes(item.metadata.region)) {
        return false;
      }
    }

    // Topic filter
    if (config.topics?.length) {
      const hasMatchingTopic = item.topics.some((t) => config.topics!.includes(t));
      if (!hasMatchingTopic) {
        return false;
      }
    }

    // Include keywords
    if (config.include_keywords?.length) {
      const text = `${item.title} ${item.summary}`.toLowerCase();
      const hasKeyword = config.include_keywords.some((k) => text.includes(k.toLowerCase()));
      if (!hasKeyword) {
        return false;
      }
    }

    // Exclude keywords
    if (config.exclude_keywords?.length) {
      const text = `${item.title} ${item.summary}`.toLowerCase();
      const hasExcluded = config.exclude_keywords.some((k) => text.includes(k.toLowerCase()));
      if (hasExcluded) {
        return false;
      }
    }

    // Age filter
    if (config.max_age_ms) {
      const itemAge = Date.now() - new Date(item.published_at).getTime();
      if (itemAge > config.max_age_ms) {
        return false;
      }
    }

    return true;
  });
}

/**
 * Deduplicate items by ID and similar titles
 */
export function deduplicateItems(items: NormalizedNewsItem[]): NormalizedNewsItem[] {
  const seen = new Map<string, NormalizedNewsItem>();
  const titleHashes = new Set<string>();

  for (const item of items) {
    // Skip if we've seen this exact ID
    if (seen.has(item.id)) {
      continue;
    }

    // Check for similar titles (to catch duplicates from different sources)
    const normalizedTitle = item.title.toLowerCase().replace(/[^a-z0-9]/g, '');
    const titleHash = hashCode(normalizedTitle);

    if (titleHashes.has(titleHash)) {
      continue;
    }

    seen.set(item.id, item);
    titleHashes.add(titleHash);
  }

  return Array.from(seen.values());
}

/**
 * Sort items by publication date (newest first)
 */
export function sortItems(items: NormalizedNewsItem[]): NormalizedNewsItem[] {
  return [...items].sort((a, b) => {
    const dateA = new Date(a.published_at).getTime();
    const dateB = new Date(b.published_at).getTime();
    return dateB - dateA;
  });
}

/**
 * Run the full news pipeline
 */
export async function runPipeline(options: PipelineOptions = {}): Promise<PipelineResult> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const startTime = Date.now();
  const errors: PipelineError[] = [];
  const stats = {
    fetched: 0,
    parsed: 0,
    filtered: 0,
    deduplicated: 0,
    duration_ms: 0,
  };

  let allItems: NormalizedNewsItem[] = [];

  // Stage 1: Fetch from sources
  logger.info('Pipeline: Starting fetch stage');

  if (opts.useGdelt) {
    try {
      const gdelt = new GdeltConnector();
      const items = await gdelt.fetchAll(opts.categories);
      allItems.push(...items);
      logger.info(`Pipeline: GDELT fetched ${items.length} items`);
    } catch (error) {
      errors.push({
        stage: 'fetch',
        source: 'GDELT',
        message: (error as Error).message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  if (opts.useRss) {
    try {
      const rss = new RSSConnector({ corsProxies: opts.corsProxies });
      const items = await rss.fetchAll(opts.categories);
      allItems.push(...items);
      logger.info(`Pipeline: RSS fetched ${items.length} items`);
    } catch (error) {
      errors.push({
        stage: 'fetch',
        source: 'RSS',
        message: (error as Error).message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  if (opts.useIntel) {
    try {
      const rss = new RSSConnector({ corsProxies: opts.corsProxies });
      const items = await rss.fetchIntel();
      allItems.push(...items);
      logger.info(`Pipeline: Intel fetched ${items.length} items`);
    } catch (error) {
      errors.push({
        stage: 'fetch',
        source: 'Intel',
        message: (error as Error).message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  stats.fetched = allItems.length;

  // Stage 2: Parse/normalize
  logger.info('Pipeline: Starting parse stage');
  try {
    allItems = allItems.map((item) => normalizeItem(item));
    stats.parsed = allItems.length;
  } catch (error) {
    errors.push({
      stage: 'parse',
      message: (error as Error).message,
      timestamp: new Date().toISOString(),
    });
  }

  // Stage 3: Filter
  if (opts.filter && Object.keys(opts.filter).length > 0) {
    logger.info('Pipeline: Starting filter stage');
    const beforeFilter = allItems.length;
    allItems = filterItems(allItems, opts.filter);
    stats.filtered = beforeFilter - allItems.length;
    logger.info(`Pipeline: Filtered out ${stats.filtered} items`);
  }

  // Stage 4: Deduplicate
  logger.info('Pipeline: Starting dedup stage');
  const beforeDedup = allItems.length;
  allItems = deduplicateItems(allItems);
  stats.deduplicated = beforeDedup - allItems.length;
  logger.info(`Pipeline: Deduplicated ${stats.deduplicated} items`);

  // Sort by date
  allItems = sortItems(allItems);

  // Stage 5: Store (if adapter provided)
  if (opts.storage) {
    logger.info('Pipeline: Starting store stage');
    try {
      await opts.storage.save(allItems);
      logger.info(`Pipeline: Stored ${allItems.length} items`);
    } catch (error) {
      errors.push({
        stage: 'store',
        message: (error as Error).message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  stats.duration_ms = Date.now() - startTime;

  logger.info(`Pipeline: Complete in ${stats.duration_ms}ms (${allItems.length} items)`);

  return {
    items: allItems,
    stats,
    errors,
  };
}

/**
 * Pipeline class for more control
 */
export class NewsPipeline {
  private options: Required<Omit<PipelineOptions, 'storage'>> & { storage?: StorageAdapter };

  constructor(options: PipelineOptions = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async run(): Promise<PipelineResult> {
    return runPipeline(this.options);
  }

  setFilter(filter: FilterConfig): this {
    this.options.filter = filter;
    return this;
  }

  setStorage(storage: StorageAdapter): this {
    this.options.storage = storage;
    return this;
  }

  setCategories(categories: NewsCategory[]): this {
    this.options.categories = categories;
    return this;
  }
}
