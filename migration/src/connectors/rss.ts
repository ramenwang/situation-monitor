/**
 * RSS Feed Connector
 *
 * Fetches and parses RSS/Atom feeds from various news sources.
 * Supports CORS proxy for browser environments.
 */

import type { FeedSource, NormalizedNewsItem, NewsCategory, RSSItem } from '../types';
import { config, FEEDS, INTEL_SOURCES, containsAlertKeyword, detectRegion, detectTopics, extractTickers } from '../utils/config';
import { generateId, parseRssDate, nowISO, stripHtml, delay, logger } from '../utils';

export interface RSSConnectorOptions {
  /** Custom CORS proxies (tried in order) */
  corsProxies?: string[];
  /** Request timeout in ms */
  timeout?: number;
}

const DEFAULT_OPTIONS: Required<RSSConnectorOptions> = {
  corsProxies: config.corsProxies,
  timeout: config.requestTimeout,
};

/**
 * Simple XML parser for RSS feeds
 * Note: For production, consider using a proper XML parser like fast-xml-parser
 */
function parseRSSXml(xml: string): RSSItem[] {
  const items: RSSItem[] = [];

  // Match <item> or <entry> tags (RSS 2.0 / Atom)
  const itemRegex = /<(?:item|entry)[\s>]([\s\S]*?)<\/(?:item|entry)>/gi;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const itemXml = match[1];
    const item: RSSItem = {};

    // Extract common fields
    const titleMatch = itemXml.match(/<title[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i);
    if (titleMatch) item.title = stripHtml(titleMatch[1].trim());

    // Link can be in href attribute (Atom) or tag content (RSS)
    const linkHrefMatch = itemXml.match(/<link[^>]*href=["']([^"']+)["'][^>]*\/?>/i);
    const linkContentMatch = itemXml.match(/<link[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/link>/i);
    item.link = linkHrefMatch?.[1] || linkContentMatch?.[1]?.trim();

    const descMatch = itemXml.match(/<(?:description|summary)[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/(?:description|summary)>/i);
    if (descMatch) item.description = stripHtml(descMatch[1].trim());

    const contentMatch = itemXml.match(/<(?:content:encoded|content)[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/(?:content:encoded|content)>/i);
    if (contentMatch) item.content = stripHtml(contentMatch[1].trim());

    // Date: pubDate (RSS) or updated/published (Atom)
    const dateMatch = itemXml.match(/<(?:pubDate|updated|published)[^>]*>([\s\S]*?)<\/(?:pubDate|updated|published)>/i);
    if (dateMatch) item.pubDate = dateMatch[1].trim();

    // Author: author, dc:creator, or creator
    const authorMatch = itemXml.match(/<(?:author|dc:creator|creator)[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/(?:author|dc:creator|creator)>/i);
    if (authorMatch) item['dc:creator'] = stripHtml(authorMatch[1].trim());

    // Only include items with at least a title or link
    if (item.title || item.link) {
      items.push(item);
    }
  }

  return items;
}

/**
 * Transform RSS item to normalized schema
 */
function transformRSSItem(
  item: RSSItem,
  source: FeedSource,
  category: NewsCategory
): NormalizedNewsItem {
  const title = item.title || '';
  const description = item.description || '';
  const content = item.content || '';
  const fullText = `${title} ${description} ${content}`;

  const alert = containsAlertKeyword(title);
  const region = detectRegion(fullText);
  const topics = detectTopics(fullText);
  const tickers = extractTickers(fullText);

  return {
    id: generateId(item.link || title, source.name),
    source: source.name,
    url: item.link || '',
    title,
    published_at: parseRssDate(item.pubDate || ''),
    fetched_at: nowISO(),
    authors: item['dc:creator'] ? [item['dc:creator']] : [],
    summary: description,
    content_text: content || description,
    tickers,
    topics,
    language: 'en',
    metadata: {
      category,
      is_alert: alert.is_alert,
      alert_keyword: alert.keyword,
      region: region ?? undefined,
      raw: item,
    },
  };
}

/**
 * Fetch RSS feed with CORS proxy fallback
 */
async function fetchWithProxy(
  url: string,
  options: Required<RSSConnectorOptions>
): Promise<string | null> {
  const proxies = options.corsProxies.length > 0 ? options.corsProxies : [''];

  for (const proxy of proxies) {
    try {
      const fetchUrl = proxy ? proxy + encodeURIComponent(url) : url;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), options.timeout);

      const response = await fetch(fetchUrl, {
        signal: controller.signal,
        headers: {
          Accept: 'application/rss+xml, application/xml, text/xml, */*',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        logger.warn(`RSS fetch failed (${response.status}):`, url);
        continue;
      }

      const text = await response.text();

      // Validate it's XML
      if (!text.includes('<') || text.includes('<!DOCTYPE html>')) {
        logger.warn(`RSS: Invalid XML response for:`, url);
        continue;
      }

      return text;
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        logger.warn(`RSS timeout:`, url);
      } else {
        logger.debug(`RSS proxy failed:`, proxy, error);
      }
    }
  }

  return null;
}

/**
 * Fetch a single RSS feed
 */
export async function fetchRSSFeed(
  source: FeedSource,
  category: NewsCategory,
  options: RSSConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  logger.debug(`Fetching RSS ${source.name}:`, source.url);

  try {
    const xml = await fetchWithProxy(source.url, opts);

    if (!xml) {
      logger.warn(`RSS ${source.name}: Failed to fetch`);
      return [];
    }

    const items = parseRSSXml(xml);
    logger.info(`RSS ${source.name}: Parsed ${items.length} items`);

    return items.map((item) => transformRSSItem(item, source, category));
  } catch (error) {
    logger.error(`RSS ${source.name}:`, error);
    return [];
  }
}

/**
 * Fetch all RSS feeds for a category
 */
export async function fetchRSSCategory(
  category: NewsCategory,
  options: RSSConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const feeds = FEEDS[category] || [];

  if (feeds.length === 0) {
    logger.debug(`RSS: No feeds configured for category: ${category}`);
    return [];
  }

  const allItems: NormalizedNewsItem[] = [];

  for (let i = 0; i < feeds.length; i++) {
    const feed = feeds[i];

    if (i > 0) {
      await delay(config.delayBetweenRequests);
    }

    const items = await fetchRSSFeed(feed, category, options);
    allItems.push(...items);
  }

  return allItems;
}

/**
 * Fetch all configured RSS feeds
 */
export async function fetchAllRSS(
  categories: NewsCategory[] = ['politics', 'tech', 'finance', 'gov', 'ai', 'intel'],
  options: RSSConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const allItems: NormalizedNewsItem[] = [];

  for (const category of categories) {
    const items = await fetchRSSCategory(category, options);
    allItems.push(...items);
  }

  return allItems;
}

/**
 * Fetch intel sources (think tanks, defense, OSINT)
 */
export async function fetchIntelFeeds(
  options: RSSConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const allItems: NormalizedNewsItem[] = [];

  for (let i = 0; i < INTEL_SOURCES.length; i++) {
    const source = INTEL_SOURCES[i];

    if (i > 0) {
      await delay(config.delayBetweenRequests);
    }

    const items = await fetchRSSFeed(source, 'intel', options);

    // Add intel-specific metadata
    const enrichedItems = items.map((item) => ({
      ...item,
      metadata: {
        ...item.metadata,
        intel_type: source.type,
        intel_topics: source.topics,
      },
    }));

    allItems.push(...enrichedItems);
  }

  return allItems;
}

/**
 * RSS Connector class for stateful usage
 */
export class RSSConnector {
  private options: Required<RSSConnectorOptions>;

  constructor(options: RSSConnectorOptions = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async fetchFeed(source: FeedSource, category: NewsCategory): Promise<NormalizedNewsItem[]> {
    return fetchRSSFeed(source, category, this.options);
  }

  async fetchCategory(category: NewsCategory): Promise<NormalizedNewsItem[]> {
    return fetchRSSCategory(category, this.options);
  }

  async fetchAll(categories?: NewsCategory[]): Promise<NormalizedNewsItem[]> {
    return fetchAllRSS(categories, this.options);
  }

  async fetchIntel(): Promise<NormalizedNewsItem[]> {
    return fetchIntelFeeds(this.options);
  }
}
