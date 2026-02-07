# Trading News Scanner

A modular news scanning and summarization toolkit extracted from [situation-monitor](https://github.com/hipcityreg/situation-monitor).

## What Was Migrated

This package extracts the core news-fetching infrastructure from a real-time intelligence dashboard:

| Component | Description |
|-----------|-------------|
| **GDELT Connector** | Fetches from Global Database of Events, Language, and Tone API |
| **RSS Connector** | Parses 30+ RSS/Atom feeds with CORS proxy support |
| **Intel Sources** | 12+ think tank, defense, and OSINT sources |
| **Keyword Detection** | Alert keywords, region detection, topic classification |
| **Ticker Extraction** | Extracts stock symbols and crypto tickers |
| **Pipeline** | Fetch → Parse → Filter → Deduplicate → Store |
| **Storage Adapters** | JSONL and SQLite output |

See [inventory.md](./inventory.md) for the complete migration mapping.

## Quick Start

### Run the Demo (No Installation Required)

The demo uses only Node.js built-in modules - no npm install needed.

**On Linux/macOS:**
```bash
cd migration
node demo.mjs
```

**On WSL (Windows Subsystem for Linux):**

WSL often uses Windows Node via PATH. Use the provided runner script:

```bash
cd migration
./run.sh
```

If you don't have Linux Node installed, the script will show instructions. Or install manually:

```bash
# Download and extract Node.js (one-time setup)
cd ~
curl -sL https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz -o node.tar.xz
tar -xf node.tar.xz

# Then run the demo
cd /path/to/migration
./run.sh
```

### Using the Full TypeScript Version

For the full TypeScript pipeline with tests:

```bash
cd migration
npm install    # Install dev dependencies
npm run demo   # Run TypeScript demo
npm test       # Run tests
```

This will:
1. Fetch news from GDELT and RSS feeds
2. Parse and normalize articles
3. Extract tickers, topics, and alerts
4. Deduplicate and sort
5. Output to `./output/news-{timestamp}.jsonl`

### Run Tests

```bash
npm test
```

## Minimal Example

```typescript
import { runPipeline, createJsonlStorage } from './src';

async function main() {
  const result = await runPipeline({
    categories: ['finance', 'tech'],
    useGdelt: true,
    useRss: true,
    storage: createJsonlStorage('./output'),
  });

  console.log(`Fetched ${result.items.length} articles`);
  console.log(`Alerts: ${result.items.filter(i => i.metadata.is_alert).length}`);
}

main();
```

## Output Schema

All news items are normalized to this schema:

```typescript
{
  "id": "stable_hash_or_uuid",
  "source": "BBC World",
  "url": "https://bbc.com/article",
  "title": "Article headline",
  "published_at": "2024-01-15T12:00:00Z",
  "fetched_at": "2024-01-15T12:05:00Z",
  "authors": ["John Doe"],
  "summary": "Brief description...",
  "content_text": "Full article text...",
  "tickers": ["AAPL", "BTC"],
  "topics": ["FINANCE", "TECH"],
  "language": "en",
  "metadata": {
    "category": "finance",
    "is_alert": true,
    "alert_keyword": "sanctions",
    "region": "EUROPE"
  }
}
```

## Adding a New News Source

### 1. Add to Feed Configuration

Edit `src/utils/config.ts`:

```typescript
export const FEEDS: Record<NewsCategory, FeedSource[]> = {
  finance: [
    // Existing feeds...
    { name: 'My New Source', url: 'https://example.com/rss.xml' },
  ],
  // ...
};
```

### 2. Create a Custom Connector (Optional)

For non-RSS sources:

```typescript
// src/connectors/custom.ts
import type { NormalizedNewsItem } from '../types';
import { generateId, nowISO } from '../utils';

export async function fetchCustomSource(): Promise<NormalizedNewsItem[]> {
  const response = await fetch('https://api.example.com/news');
  const data = await response.json();

  return data.articles.map(article => ({
    id: generateId(article.url, 'custom'),
    source: 'Custom Source',
    url: article.url,
    title: article.title,
    published_at: article.date,
    fetched_at: nowISO(),
    authors: [],
    summary: article.summary || '',
    content_text: '',
    tickers: [],
    topics: [],
    language: 'en',
    metadata: {},
  }));
}
```

### 3. Add to Pipeline

```typescript
import { runPipeline, createJsonlStorage } from './src';
import { fetchCustomSource } from './src/connectors/custom';

async function main() {
  // Fetch from custom source
  const customItems = await fetchCustomSource();

  // Run standard pipeline (will merge and dedupe)
  const result = await runPipeline({
    useGdelt: true,
    useRss: false,
    storage: createJsonlStorage('./output'),
  });

  // Combine
  const allItems = [...customItems, ...result.items];
}
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Optional API keys
FINNHUB_API_KEY=your_key_here
FRED_API_KEY=your_key_here

# CORS proxies (for RSS in browser)
CORS_PROXY_PRIMARY=https://api.allorigins.win/raw?url=

# Request settings
REQUEST_TIMEOUT=15000
DELAY_BETWEEN_REQUESTS=500

# Output
OUTPUT_DIR=./output
DEBUG=false
```

## Limitations & Missing Pieces

### Not Included

1. **Full Article Scraping** - Only fetches RSS/API summaries, not full article text
2. **Summarization** - No LLM integration for summarizing articles
3. **Sentiment Analysis** - Topic detection only, no sentiment scoring
4. **Historical Data** - No database backfill or historical fetch
5. **Scheduling** - No built-in cron/polling (see below)
6. **Market Data** - Finnhub/CoinGecko connectors not migrated (can add)

### Browser vs Node.js

- **Node.js**: Works out of the box, no CORS issues
- **Browser**: Requires CORS proxy for RSS feeds

### Adding Scheduling

```typescript
import cron from 'node-cron';
import { runPipeline, createJsonlStorage } from './src';

// Run every 5 minutes
cron.schedule('*/5 * * * *', async () => {
  await runPipeline({
    storage: createJsonlStorage('./output'),
  });
});
```

### Adding Summarization

```typescript
import { runPipeline } from './src';
import OpenAI from 'openai';

const openai = new OpenAI();

async function summarizeItems(items) {
  for (const item of items) {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{
        role: 'user',
        content: `Summarize this news for a trader:\n\n${item.title}\n\n${item.summary}`,
      }],
    });

    item.metadata.ai_summary = response.choices[0].message.content;
  }
  return items;
}
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for:
- Component diagram
- Data flow diagram
- Module structure
- Extension points

## Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

Tests use Vitest with mocked network calls.

## License

MIT
