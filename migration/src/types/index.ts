/**
 * Normalized News Item Schema
 *
 * All news items from any source are transformed to this schema.
 */
export interface NormalizedNewsItem {
  /** Stable hash or UUID for deduplication */
  id: string;
  /** Source name (e.g., "BBC World", "GDELT", "Hacker News") */
  source: string;
  /** Original article URL */
  url: string;
  /** Article title/headline */
  title: string;
  /** ISO8601 publication timestamp */
  published_at: string;
  /** ISO8601 fetch timestamp */
  fetched_at: string;
  /** Author names if available */
  authors: string[];
  /** Article summary or description */
  summary: string;
  /** Full article text if available */
  content_text: string;
  /** Detected stock/crypto tickers (e.g., ["AAPL", "BTC"]) */
  tickers: string[];
  /** Detected topics (e.g., ["CONFLICT", "CYBER", "FINANCE"]) */
  topics: string[];
  /** Content language (e.g., "en") */
  language: string;
  /** Additional metadata */
  metadata: NewsMetadata;
}

/**
 * Extended metadata for news items
 */
export interface NewsMetadata {
  /** News category */
  category?: NewsCategory;
  /** Is this an alert-worthy item? */
  is_alert?: boolean;
  /** Which alert keyword triggered */
  alert_keyword?: string;
  /** Detected geographic region */
  region?: string;
  /** Original source domain */
  domain?: string;
  /** Image URL if available */
  image_url?: string;
  /** Raw data from original source */
  raw?: unknown;
}

/**
 * News category types
 */
export type NewsCategory = 'politics' | 'tech' | 'finance' | 'gov' | 'ai' | 'intel' | 'general';

/**
 * RSS Feed source configuration
 */
export interface FeedSource {
  /** Display name */
  name: string;
  /** RSS feed URL */
  url: string;
  /** Category for classification */
  category?: NewsCategory;
}

/**
 * Intel source with additional metadata
 */
export interface IntelSource extends FeedSource {
  type: 'think-tank' | 'defense' | 'regional' | 'osint' | 'govt' | 'cyber';
  topics: string[];
  region?: string;
}

/**
 * GDELT API response types
 */
export interface GdeltArticle {
  title: string;
  url: string;
  seendate: string;
  domain: string;
  socialimage?: string;
  language?: string;
}

export interface GdeltResponse {
  articles?: GdeltArticle[];
}

/**
 * RSS feed item (parsed from XML)
 */
export interface RSSItem {
  title?: string;
  link?: string;
  description?: string;
  pubDate?: string;
  author?: string;
  'dc:creator'?: string;
  content?: string;
  'content:encoded'?: string;
}

/**
 * Cache entry structure
 */
export interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  ttl: number;
  stale_until: number;
}

/**
 * Service configuration
 */
export interface ServiceConfig {
  id: string;
  base_url: string | null;
  timeout: number;
  retries: number;
  cache?: {
    ttl: number;
    stale_while_revalidate: boolean;
  };
  circuit_breaker?: {
    failure_threshold: number;
    reset_timeout: number;
  };
}

/**
 * Fetch result with cache metadata
 */
export interface FetchResult<T = unknown> {
  data: T;
  from_cache: false | 'memory' | 'storage' | 'fallback' | 'stale-fallback';
  stale?: boolean;
  error?: string;
}

/**
 * Pipeline stage result
 */
export interface PipelineResult {
  items: NormalizedNewsItem[];
  stats: {
    fetched: number;
    parsed: number;
    filtered: number;
    deduplicated: number;
    duration_ms: number;
  };
  errors: PipelineError[];
}

export interface PipelineError {
  stage: 'fetch' | 'parse' | 'filter' | 'dedup' | 'store';
  source?: string;
  message: string;
  timestamp: string;
}

/**
 * Storage adapter interface
 */
export interface StorageAdapter {
  save(items: NormalizedNewsItem[]): Promise<void>;
  load(): Promise<NormalizedNewsItem[]>;
  clear(): Promise<void>;
}

/**
 * Filter configuration
 */
export interface FilterConfig {
  /** Only include items matching these keywords */
  include_keywords?: string[];
  /** Exclude items matching these keywords */
  exclude_keywords?: string[];
  /** Only include these categories */
  categories?: NewsCategory[];
  /** Only include these regions */
  regions?: string[];
  /** Only include these topics */
  topics?: string[];
  /** Maximum age in milliseconds */
  max_age_ms?: number;
}
