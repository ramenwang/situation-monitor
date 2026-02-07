/**
 * Connector Tests
 *
 * Tests for GDELT and RSS connectors with mocked network.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock fetch before importing connectors
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Now import connectors
import { fetchGdeltCategory } from '../src/connectors/gdelt';
import { fetchRSSFeed } from '../src/connectors/rss';

describe('GDELT Connector', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should fetch and transform GDELT articles', async () => {
    const mockResponse = {
      articles: [
        {
          title: 'Test Article About Finance',
          url: 'https://example.com/article1',
          seendate: '20240115T120000Z',
          domain: 'example.com',
          socialimage: 'https://example.com/image.jpg',
        },
        {
          title: 'Another Tech Article',
          url: 'https://example.com/article2',
          seendate: '20240115T110000Z',
          domain: 'tech.com',
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify(mockResponse),
    });

    const items = await fetchGdeltCategory('finance');

    expect(items).toHaveLength(2);
    expect(items[0].title).toBe('Test Article About Finance');
    expect(items[0].source).toBe('example.com');
    expect(items[0].url).toBe('https://example.com/article1');
    expect(items[0].published_at).toBe('2024-01-15T12:00:00Z');
    expect(items[0].metadata.category).toBe('finance');
    expect(items[0].metadata.image_url).toBe('https://example.com/image.jpg');
  });

  it('should handle empty response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({}),
    });

    const items = await fetchGdeltCategory('politics');
    expect(items).toHaveLength(0);
  });

  it('should handle network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const items = await fetchGdeltCategory('tech');
    expect(items).toHaveLength(0);
  });

  it('should handle non-JSON responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'text/html' }),
      text: async () => '<html>Error page</html>',
    });

    const items = await fetchGdeltCategory('ai');
    expect(items).toHaveLength(0);
  });

  it('should detect topics in article titles', async () => {
    const mockResponse = {
      articles: [
        {
          title: 'Cyber attack targets military defense systems',
          url: 'https://example.com/cyber',
          seendate: '20240115T120000Z',
          domain: 'security.com',
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify(mockResponse),
    });

    const items = await fetchGdeltCategory('intel');

    expect(items[0].topics).toContain('CYBER');
    expect(items[0].topics).toContain('DEFENSE');
  });
});

describe('RSS Connector', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should fetch and parse RSS feed', async () => {
    const mockRss = `
      <?xml version="1.0" encoding="UTF-8"?>
      <rss version="2.0">
        <channel>
          <title>Test Feed</title>
          <item>
            <title>Breaking News: Market Rally</title>
            <link>https://example.com/news/1</link>
            <description>Markets are up today.</description>
            <pubDate>Mon, 15 Jan 2024 12:00:00 +0000</pubDate>
            <dc:creator>John Doe</dc:creator>
          </item>
          <item>
            <title>Tech Company Announces Layoffs</title>
            <link>https://example.com/news/2</link>
            <description>Major tech company cutting jobs.</description>
            <pubDate>Mon, 15 Jan 2024 11:00:00 +0000</pubDate>
          </item>
        </channel>
      </rss>
    `;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => mockRss,
    });

    const items = await fetchRSSFeed(
      { name: 'Test Feed', url: 'https://example.com/feed.xml' },
      'finance',
      { corsProxies: [] }
    );

    expect(items).toHaveLength(2);
    expect(items[0].title).toBe('Breaking News: Market Rally');
    expect(items[0].source).toBe('Test Feed');
    expect(items[0].summary).toBe('Markets are up today.');
    expect(items[0].metadata.category).toBe('finance');
  });

  it('should parse Atom feeds', async () => {
    const mockAtom = `
      <?xml version="1.0" encoding="UTF-8"?>
      <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Atom Feed</title>
        <entry>
          <title>Atom Article</title>
          <link href="https://example.com/atom/1"/>
          <summary>This is an Atom entry.</summary>
          <updated>2024-01-15T12:00:00Z</updated>
          <author><name>Jane Smith</name></author>
        </entry>
      </feed>
    `;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => mockAtom,
    });

    const items = await fetchRSSFeed(
      { name: 'Atom Feed', url: 'https://example.com/atom.xml' },
      'tech',
      { corsProxies: [] }
    );

    expect(items).toHaveLength(1);
    expect(items[0].title).toBe('Atom Article');
    expect(items[0].url).toBe('https://example.com/atom/1');
  });

  it('should handle CDATA sections', async () => {
    const mockRss = `
      <?xml version="1.0"?>
      <rss version="2.0">
        <channel>
          <item>
            <title><![CDATA[Article with <b>HTML</b> in title]]></title>
            <link>https://example.com/cdata</link>
            <description><![CDATA[<p>HTML content here</p>]]></description>
          </item>
        </channel>
      </rss>
    `;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => mockRss,
    });

    const items = await fetchRSSFeed(
      { name: 'CDATA Feed', url: 'https://example.com/cdata.xml' },
      'general',
      { corsProxies: [] }
    );

    expect(items[0].title).toBe('Article with HTML in title');
    expect(items[0].summary).toBe('HTML content here');
  });

  it('should extract tickers from content', async () => {
    const mockRss = `
      <?xml version="1.0"?>
      <rss version="2.0">
        <channel>
          <item>
            <title>$AAPL and $GOOGL lead tech rally</title>
            <link>https://example.com/stocks</link>
            <description>Apple Inc (AAPL stock) and Google lead gains. Bitcoin BTC also up.</description>
          </item>
        </channel>
      </rss>
    `;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => mockRss,
    });

    const items = await fetchRSSFeed(
      { name: 'Stock Feed', url: 'https://example.com/stocks.xml' },
      'finance',
      { corsProxies: [] }
    );

    expect(items[0].tickers).toContain('AAPL');
    expect(items[0].tickers).toContain('GOOGL');
    expect(items[0].tickers).toContain('BTC');
  });

  it('should handle fetch errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const items = await fetchRSSFeed(
      { name: 'Error Feed', url: 'https://example.com/error.xml' },
      'politics',
      { corsProxies: [] }
    );

    expect(items).toHaveLength(0);
  });

  it('should try multiple CORS proxies on failure', async () => {
    // First proxy fails
    mockFetch.mockRejectedValueOnce(new Error('Proxy 1 failed'));
    // Second proxy succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => `
        <rss version="2.0">
          <channel>
            <item>
              <title>Success</title>
              <link>https://example.com/success</link>
            </item>
          </channel>
        </rss>
      `,
    });

    const items = await fetchRSSFeed(
      { name: 'Proxy Test', url: 'https://example.com/feed.xml' },
      'general',
      { corsProxies: ['https://proxy1.com/?url=', 'https://proxy2.com/?url='] }
    );

    expect(items).toHaveLength(1);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
