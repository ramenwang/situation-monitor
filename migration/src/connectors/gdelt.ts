/**
 * GDELT News API Connector
 *
 * Fetches news from the Global Database of Events, Language, and Tone (GDELT).
 * https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
 */

import type { GdeltResponse, GdeltArticle, NormalizedNewsItem, NewsCategory } from '../types';
import { config, GDELT_QUERIES, containsAlertKeyword, detectRegion, detectTopics } from '../utils/config';
import { generateId, parseGdeltDate, nowISO, delay, logger } from '../utils';

export interface GdeltConnectorOptions {
  /** Number of articles to fetch per category (max 250) */
  maxRecords?: number;
  /** Timespan for articles (e.g., "7d", "24h") */
  timespan?: string;
  /** Language filter */
  language?: string;
  /** Custom CORS proxy URL (optional) */
  corsProxy?: string;
}

const DEFAULT_OPTIONS: Required<GdeltConnectorOptions> = {
  maxRecords: 20,
  timespan: '7d',
  language: 'english',
  corsProxy: '',
};

/**
 * Transform a GDELT article to normalized schema
 */
function transformArticle(
  article: GdeltArticle,
  category: NewsCategory,
  index: number
): NormalizedNewsItem {
  const title = article.title || '';
  const alert = containsAlertKeyword(title);
  const region = detectRegion(title);
  const topics = detectTopics(title);

  return {
    id: generateId(article.url, `gdelt-${category}`),
    source: article.domain || 'GDELT',
    url: article.url,
    title,
    published_at: parseGdeltDate(article.seendate),
    fetched_at: nowISO(),
    authors: [],
    summary: '',
    content_text: '',
    tickers: [],
    topics,
    language: article.language || 'en',
    metadata: {
      category,
      is_alert: alert.is_alert,
      alert_keyword: alert.keyword,
      region: region ?? undefined,
      domain: article.domain,
      image_url: article.socialimage,
      raw: article,
    },
  };
}

/**
 * Build GDELT API URL
 */
function buildGdeltUrl(category: NewsCategory, options: Required<GdeltConnectorOptions>): string {
  const baseQuery = GDELT_QUERIES[category];
  if (!baseQuery) {
    throw new Error(`Unknown category: ${category}`);
  }

  const fullQuery = `${baseQuery} sourcelang:${options.language}`;
  const params = new URLSearchParams({
    query: fullQuery,
    timespan: options.timespan,
    mode: 'artlist',
    maxrecords: options.maxRecords.toString(),
    format: 'json',
    sort: 'date',
  });

  return `${config.gdeltBaseUrl}/api/v2/doc/doc?${params.toString()}`;
}

/**
 * Fetch news from GDELT for a single category
 */
export async function fetchGdeltCategory(
  category: NewsCategory,
  options: GdeltConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const url = buildGdeltUrl(category, opts);

  logger.debug(`Fetching GDELT ${category}:`, url);

  try {
    // Use CORS proxy if specified
    const fetchUrl = opts.corsProxy ? opts.corsProxy + encodeURIComponent(url) : url;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.requestTimeout);

    const response = await fetch(fetchUrl, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      logger.warn(`GDELT ${category}: Non-JSON response:`, contentType);
      return [];
    }

    const text = await response.text();
    let data: GdeltResponse;

    try {
      data = JSON.parse(text);
    } catch {
      logger.warn(`GDELT ${category}: Invalid JSON:`, text.slice(0, 100));
      return [];
    }

    if (!data?.articles) {
      logger.debug(`GDELT ${category}: No articles in response`);
      return [];
    }

    logger.info(`GDELT ${category}: Fetched ${data.articles.length} articles`);

    return data.articles.map((article, index) => transformArticle(article, category, index));
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      logger.error(`GDELT ${category}: Request timeout`);
    } else {
      logger.error(`GDELT ${category}:`, error);
    }
    return [];
  }
}

/**
 * Fetch news from all GDELT categories
 */
export async function fetchAllGdelt(
  categories: NewsCategory[] = ['politics', 'tech', 'finance', 'gov', 'ai', 'intel'],
  options: GdeltConnectorOptions = {}
): Promise<NormalizedNewsItem[]> {
  const allItems: NormalizedNewsItem[] = [];

  for (let i = 0; i < categories.length; i++) {
    const category = categories[i];

    // Add delay between requests to avoid rate limiting
    if (i > 0) {
      await delay(config.delayBetweenRequests);
    }

    const items = await fetchGdeltCategory(category, options);
    allItems.push(...items);
  }

  return allItems;
}

/**
 * GDELT Connector class for stateful usage
 */
export class GdeltConnector {
  private options: Required<GdeltConnectorOptions>;

  constructor(options: GdeltConnectorOptions = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async fetchCategory(category: NewsCategory): Promise<NormalizedNewsItem[]> {
    return fetchGdeltCategory(category, this.options);
  }

  async fetchAll(
    categories: NewsCategory[] = ['politics', 'tech', 'finance', 'gov', 'ai', 'intel']
  ): Promise<NormalizedNewsItem[]> {
    return fetchAllGdelt(categories, this.options);
  }
}
