/**
 * Configuration for the news pipeline
 *
 * All configuration is loaded from environment variables with sensible defaults.
 * Create a .env file based on .env.example to override.
 */

import type { FeedSource, IntelSource, NewsCategory, ServiceConfig } from '../types';

/**
 * Load environment variable with fallback
 */
function env(key: string, defaultValue: string = ''): string {
  if (typeof process !== 'undefined' && process.env) {
    return process.env[key] ?? defaultValue;
  }
  return defaultValue;
}

/**
 * Main configuration object
 */
export const config = {
  /** Debug mode - enables verbose logging */
  debug: env('DEBUG', 'false') === 'true',

  /** API Keys */
  finnhubApiKey: env('FINNHUB_API_KEY', ''),
  fredApiKey: env('FRED_API_KEY', ''),

  /** CORS Proxies for RSS feeds (order matters - primary first) */
  corsProxies: [
    env('CORS_PROXY_PRIMARY', 'https://api.allorigins.win/raw?url='),
    env('CORS_PROXY_FALLBACK', 'https://corsproxy.io/?url='),
  ].filter(Boolean),

  /** API base URLs */
  gdeltBaseUrl: 'https://api.gdeltproject.org',
  finnhubBaseUrl: 'https://finnhub.io/api/v1',
  coinGeckoBaseUrl: 'https://api.coingecko.com/api/v3',

  /** Request timing */
  requestTimeout: parseInt(env('REQUEST_TIMEOUT', '15000'), 10),
  delayBetweenRequests: parseInt(env('DELAY_BETWEEN_REQUESTS', '500'), 10),

  /** Cache settings */
  cacheTtlNews: parseInt(env('CACHE_TTL_NEWS', '300000'), 10), // 5 minutes
  cacheTtlMarkets: parseInt(env('CACHE_TTL_MARKETS', '60000'), 10), // 1 minute

  /** Circuit breaker settings */
  circuitBreakerThreshold: parseInt(env('CIRCUIT_BREAKER_THRESHOLD', '3'), 10),
  circuitBreakerResetMs: parseInt(env('CIRCUIT_BREAKER_RESET_MS', '60000'), 10),

  /** Output settings */
  outputDir: env('OUTPUT_DIR', './output'),
  outputFormat: env('OUTPUT_FORMAT', 'jsonl') as 'jsonl' | 'sqlite',
};

/**
 * Alert keywords that indicate high-priority news
 */
export const ALERT_KEYWORDS = [
  'war',
  'invasion',
  'military',
  'nuclear',
  'sanctions',
  'missile',
  'attack',
  'troops',
  'conflict',
  'strike',
  'bomb',
  'casualties',
  'ceasefire',
  'treaty',
  'nato',
  'coup',
  'martial law',
  'emergency',
  'assassination',
  'terrorist',
  'hostage',
  'evacuation',
] as const;

/**
 * Region detection keywords
 */
export const REGION_KEYWORDS: Record<string, string[]> = {
  EUROPE: ['nato', 'eu', 'european', 'ukraine', 'russia', 'germany', 'france', 'uk', 'britain', 'poland'],
  MENA: ['iran', 'israel', 'saudi', 'syria', 'iraq', 'gaza', 'lebanon', 'yemen', 'houthi', 'middle east'],
  APAC: ['china', 'taiwan', 'japan', 'korea', 'indo-pacific', 'south china sea', 'asean', 'philippines'],
  AMERICAS: ['us', 'america', 'canada', 'mexico', 'brazil', 'venezuela', 'latin'],
  AFRICA: ['africa', 'sahel', 'niger', 'sudan', 'ethiopia', 'somalia'],
};

/**
 * Topic detection keywords
 */
export const TOPIC_KEYWORDS: Record<string, string[]> = {
  CYBER: ['cyber', 'hack', 'ransomware', 'malware', 'breach', 'apt', 'vulnerability'],
  NUCLEAR: ['nuclear', 'icbm', 'warhead', 'nonproliferation', 'uranium', 'plutonium'],
  CONFLICT: ['war', 'military', 'troops', 'invasion', 'strike', 'missile', 'combat', 'offensive'],
  INTEL: ['intelligence', 'espionage', 'spy', 'cia', 'mossad', 'fsb', 'covert'],
  DEFENSE: ['pentagon', 'dod', 'defense', 'military', 'army', 'navy', 'air force'],
  DIPLO: ['diplomat', 'embassy', 'treaty', 'sanctions', 'talks', 'summit', 'bilateral'],
  FINANCE: ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment', 'recession', 'rally', 'crash'],
  CRYPTO: ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi', 'nft', 'stablecoin'],
  TECH: ['ai', 'artificial intelligence', 'machine learning', 'startup', 'ipo', 'acquisition', 'layoff'],
};

/**
 * Stock/crypto ticker patterns for extraction
 */
export const TICKER_PATTERNS = [
  // Stock tickers: $AAPL or AAPL (1-5 uppercase letters)
  /\$([A-Z]{1,5})\b/g,
  /\b([A-Z]{2,5})\b(?=\s+(?:stock|shares|inc|corp|ltd))/gi,
  // Crypto: BTC, ETH, etc.
  /\b(BTC|ETH|SOL|XRP|ADA|DOGE|DOT|AVAX|MATIC|LINK)\b/gi,
];

/**
 * RSS feed sources organized by category
 */
export const FEEDS: Record<NewsCategory, FeedSource[]> = {
  politics: [
    { name: 'BBC World', url: 'https://feeds.bbci.co.uk/news/world/rss.xml' },
    { name: 'NPR News', url: 'https://feeds.npr.org/1001/rss.xml' },
    { name: 'Guardian World', url: 'https://www.theguardian.com/world/rss' },
    { name: 'NYT World', url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml' },
  ],
  tech: [
    { name: 'Hacker News', url: 'https://hnrss.org/frontpage' },
    { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/technology-lab' },
    { name: 'The Verge', url: 'https://www.theverge.com/rss/index.xml' },
    { name: 'MIT Tech Review', url: 'https://www.technologyreview.com/feed/' },
  ],
  finance: [
    { name: 'CNBC', url: 'https://www.cnbc.com/id/100003114/device/rss/rss.html' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/news/rssindex' },
    { name: 'BBC Business', url: 'https://feeds.bbci.co.uk/news/business/rss.xml' },
  ],
  gov: [
    { name: 'White House', url: 'https://www.whitehouse.gov/news/feed/' },
    { name: 'Federal Reserve', url: 'https://www.federalreserve.gov/feeds/press_all.xml' },
    { name: 'SEC Announcements', url: 'https://www.sec.gov/news/pressreleases.rss' },
    { name: 'DoD News', url: 'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=10&ContentType=1&Site=945' },
  ],
  ai: [
    { name: 'OpenAI Blog', url: 'https://openai.com/news/rss.xml' },
    { name: 'ArXiv AI', url: 'https://rss.arxiv.org/rss/cs.AI' },
  ],
  intel: [
    { name: 'CSIS', url: 'https://www.csis.org/analysis/feed' },
    { name: 'Brookings', url: 'https://www.brookings.edu/feed/' },
  ],
  general: [],
};

/**
 * Intel sources with additional metadata
 */
export const INTEL_SOURCES: IntelSource[] = [
  { name: 'CSIS', url: 'https://www.csis.org/analysis/feed', type: 'think-tank', topics: ['defense', 'geopolitics'] },
  { name: 'Brookings', url: 'https://www.brookings.edu/feed/', type: 'think-tank', topics: ['policy', 'geopolitics'] },
  { name: 'CFR', url: 'https://www.cfr.org/rss.xml', type: 'think-tank', topics: ['foreign-policy'] },
  { name: 'Defense One', url: 'https://www.defenseone.com/rss/all/', type: 'defense', topics: ['military', 'defense'] },
  { name: 'War on Rocks', url: 'https://warontherocks.com/feed/', type: 'defense', topics: ['military', 'strategy'] },
  { name: 'Breaking Defense', url: 'https://breakingdefense.com/feed/', type: 'defense', topics: ['military', 'defense'] },
  { name: 'The Diplomat', url: 'https://thediplomat.com/feed/', type: 'regional', topics: ['asia-pacific'], region: 'APAC' },
  { name: 'Al-Monitor', url: 'https://www.al-monitor.com/rss', type: 'regional', topics: ['middle-east'], region: 'MENA' },
  { name: 'Bellingcat', url: 'https://www.bellingcat.com/feed/', type: 'osint', topics: ['investigation', 'osint'] },
  { name: 'CISA Alerts', url: 'https://www.cisa.gov/uscert/ncas/alerts.xml', type: 'cyber', topics: ['cyber', 'security'] },
  { name: 'Krebs Security', url: 'https://krebsonsecurity.com/feed/', type: 'cyber', topics: ['cyber', 'security'] },
];

/**
 * GDELT query templates by category
 */
export const GDELT_QUERIES: Record<NewsCategory, string> = {
  politics: '(politics OR government OR election OR congress)',
  tech: '(technology OR software OR startup OR "silicon valley")',
  finance: '(finance OR "stock market" OR economy OR banking)',
  gov: '("federal government" OR "white house" OR congress OR regulation)',
  ai: '("artificial intelligence" OR "machine learning" OR AI OR ChatGPT)',
  intel: '(intelligence OR security OR military OR defense)',
  general: '',
};

/**
 * Service configurations for resilience layer
 */
export const SERVICE_CONFIGS: Record<string, ServiceConfig> = {
  GDELT: {
    id: 'gdelt',
    base_url: 'https://api.gdeltproject.org',
    timeout: 15000,
    retries: 1,
    cache: { ttl: 180000, stale_while_revalidate: true },
    circuit_breaker: { failure_threshold: 2, reset_timeout: 60000 },
  },
  COINGECKO: {
    id: 'coingecko',
    base_url: 'https://api.coingecko.com',
    timeout: 10000,
    retries: 2,
    cache: { ttl: 60000, stale_while_revalidate: false },
    circuit_breaker: { failure_threshold: 3, reset_timeout: 120000 },
  },
  RSS: {
    id: 'rss',
    base_url: null,
    timeout: 12000,
    retries: 1,
    cache: { ttl: 300000, stale_while_revalidate: true },
    circuit_breaker: { failure_threshold: 5, reset_timeout: 120000 },
  },
};

/**
 * Check if an alert keyword is in text
 */
export function containsAlertKeyword(text: string): { is_alert: boolean; keyword?: string } {
  const lowerText = text.toLowerCase();
  for (const keyword of ALERT_KEYWORDS) {
    if (lowerText.includes(keyword)) {
      return { is_alert: true, keyword };
    }
  }
  return { is_alert: false };
}

/**
 * Detect region from text
 */
export function detectRegion(text: string): string | null {
  const lowerText = text.toLowerCase();
  for (const [region, keywords] of Object.entries(REGION_KEYWORDS)) {
    if (keywords.some((k) => lowerText.includes(k))) {
      return region;
    }
  }
  return null;
}

/**
 * Detect topics from text
 */
export function detectTopics(text: string): string[] {
  const lowerText = text.toLowerCase();
  const detected: string[] = [];
  for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
    if (keywords.some((k) => lowerText.includes(k))) {
      detected.push(topic);
    }
  }
  return detected;
}

/**
 * Extract tickers from text
 */
export function extractTickers(text: string): string[] {
  const tickers = new Set<string>();

  for (const pattern of TICKER_PATTERNS) {
    // Reset lastIndex for global patterns
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      tickers.add(match[1].toUpperCase());
    }
  }

  return Array.from(tickers);
}
