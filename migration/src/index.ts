/**
 * Trading News Scanner - Migration Package
 *
 * Extracted from situation-monitor for reuse in trading news applications.
 */

// Types
export * from './types';

// Configuration
export { config, ALERT_KEYWORDS, REGION_KEYWORDS, TOPIC_KEYWORDS, FEEDS, INTEL_SOURCES } from './utils/config';
export { containsAlertKeyword, detectRegion, detectTopics, extractTickers } from './utils/config';

// Utilities
export {
  hashCode,
  generateId,
  parseGdeltDate,
  parseRssDate,
  nowISO,
  delay,
  getBackoffDelay,
  stripHtml,
  truncate,
  extractDomain,
  logger,
} from './utils';

// Connectors
export { GdeltConnector, fetchGdeltCategory, fetchAllGdelt } from './connectors/gdelt';
export { RSSConnector, fetchRSSFeed, fetchRSSCategory, fetchAllRSS, fetchIntelFeeds } from './connectors/rss';

// Parsers
export { cleanText, extractSummary, normalizeItem, parseItems, parseAuthors, parseDate } from './parsers';

// Pipeline
export { NewsPipeline, runPipeline, filterItems, deduplicateItems, sortItems } from './pipeline';

// Storage
export { JsonlStorage, createJsonlStorage } from './storage/jsonl';
export { SqliteStorage, createSqliteStorage } from './storage/sqlite';
