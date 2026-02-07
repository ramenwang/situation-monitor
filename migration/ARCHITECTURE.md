# Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEWS PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │  CONNECTORS │     │   PARSERS   │     │   PIPELINE  │     │  STORAGE  │ │
│  │             │     │             │     │             │     │           │ │
│  │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌───────┐ │ │
│  │ │  GDELT  │─┼────▶│ │normalize│─┼────▶│ │ filter  │─┼────▶│ │ JSONL │ │ │
│  │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │     │ └───────┘ │ │
│  │             │     │             │     │      │      │     │           │ │
│  │ ┌─────────┐ │     │ ┌─────────┐ │     │      ▼      │     │ ┌───────┐ │ │
│  │ │   RSS   │─┼────▶│ │cleanText│─┼────▶│ ┌─────────┐ │     │ │SQLite │ │ │
│  │ └─────────┘ │     │ └─────────┘ │     │ │  dedup  │ │     │ └───────┘ │ │
│  │             │     │             │     │ └─────────┘ │     │           │ │
│  │ ┌─────────┐ │     │ ┌─────────┐ │     │      │      │     │           │ │
│  │ │  Intel  │─┼────▶│ │ extract │ │     │      ▼      │     │           │ │
│  │ └─────────┘ │     │ │ topics  │ │     │ ┌─────────┐ │     │           │ │
│  │             │     │ └─────────┘ │     │ │  sort   │ │     │           │ │
│  └─────────────┘     └─────────────┘     │ └─────────┘ │     └───────────┘ │
│                                          └─────────────┘                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                              CONFIGURATION                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  config.ts: feeds, keywords, topics, API settings, CORS proxies       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                 TYPES                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  NormalizedNewsItem, FeedSource, PipelineResult, StorageAdapter        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
                                    ┌──────────────────────────┐
                                    │     External Sources     │
                                    └──────────────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
           │    GDELT     │           │  RSS Feeds   │           │ Intel Feeds  │
           │   (30+ sources)          │   (30+)      │           │   (12+)      │
           └──────────────┘           └──────────────┘           └──────────────┘
                    │                          │                          │
                    │   HTTP + CORS Proxy      │                          │
                    │         (optional)       │                          │
                    └──────────────────────────┼──────────────────────────┘
                                               │
                                               ▼
                                    ┌──────────────────────────┐
                                    │     Raw Articles         │
                                    │  (GdeltArticle, RSSItem) │
                                    └──────────────────────────┘
                                               │
                                               │ Transform
                                               ▼
                                    ┌──────────────────────────┐
                                    │   Normalized Items       │
                                    │   (NormalizedNewsItem)   │
                                    │                          │
                                    │   - id                   │
                                    │   - source               │
                                    │   - url                  │
                                    │   - title                │
                                    │   - published_at         │
                                    │   - fetched_at           │
                                    │   - authors              │
                                    │   - summary              │
                                    │   - content_text         │
                                    │   - tickers              │
                                    │   - topics               │
                                    │   - language             │
                                    │   - metadata             │
                                    └──────────────────────────┘
                                               │
                                               │ Parse & Enrich
                                               ▼
                                    ┌──────────────────────────┐
                                    │     Enriched Items       │
                                    │                          │
                                    │   + Alert detection      │
                                    │   + Region detection     │
                                    │   + Topic extraction     │
                                    │   + Ticker extraction    │
                                    │   + HTML cleaning        │
                                    └──────────────────────────┘
                                               │
                                               │ Filter
                                               ▼
                                    ┌──────────────────────────┐
                                    │    Filtered Items        │
                                    │                          │
                                    │   - Category filter      │
                                    │   - Region filter        │
                                    │   - Topic filter         │
                                    │   - Keyword include/     │
                                    │     exclude              │
                                    │   - Max age filter       │
                                    └──────────────────────────┘
                                               │
                                               │ Deduplicate
                                               ▼
                                    ┌──────────────────────────┐
                                    │   Deduplicated Items     │
                                    │                          │
                                    │   - By ID                │
                                    │   - By title similarity  │
                                    └──────────────────────────┘
                                               │
                                               │ Sort
                                               ▼
                                    ┌──────────────────────────┐
                                    │    Sorted Items          │
                                    │   (newest first)         │
                                    └──────────────────────────┘
                                               │
                                               │ Store
                                               ▼
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
           │    JSONL     │           │    SQLite    │           │   (custom)   │
           │  (default)   │           │  (optional)  │           │              │
           └──────────────┘           └──────────────┘           └──────────────┘
```

## Module Structure

```
migration/
├── src/
│   ├── index.ts              # Main exports
│   │
│   ├── types/
│   │   └── index.ts          # TypeScript interfaces
│   │                         #   - NormalizedNewsItem
│   │                         #   - FeedSource, IntelSource
│   │                         #   - PipelineResult
│   │                         #   - StorageAdapter
│   │
│   ├── connectors/
│   │   ├── index.ts          # Re-exports
│   │   ├── gdelt.ts          # GDELT API connector
│   │   │                     #   - fetchGdeltCategory()
│   │   │                     #   - fetchAllGdelt()
│   │   │                     #   - GdeltConnector class
│   │   │
│   │   └── rss.ts            # RSS/Atom feed connector
│   │                         #   - fetchRSSFeed()
│   │                         #   - fetchRSSCategory()
│   │                         #   - fetchAllRSS()
│   │                         #   - fetchIntelFeeds()
│   │                         #   - RSSConnector class
│   │
│   ├── parsers/
│   │   └── index.ts          # Text processing
│   │                         #   - cleanText()
│   │                         #   - extractSummary()
│   │                         #   - normalizeItem()
│   │                         #   - parseAuthors()
│   │                         #   - parseDate()
│   │
│   ├── pipeline/
│   │   └── index.ts          # Orchestration
│   │                         #   - runPipeline()
│   │                         #   - filterItems()
│   │                         #   - deduplicateItems()
│   │                         #   - sortItems()
│   │                         #   - NewsPipeline class
│   │
│   ├── storage/
│   │   ├── index.ts          # Re-exports
│   │   ├── jsonl.ts          # JSONL file adapter
│   │   │                     #   - JsonlStorage class
│   │   │                     #   - createJsonlStorage()
│   │   │
│   │   └── sqlite.ts         # SQLite adapter
│   │                         #   - SqliteStorage class
│   │                         #   - createSqliteStorage()
│   │
│   └── utils/
│       ├── index.ts          # Utility functions
│       │                     #   - hashCode()
│       │                     #   - generateId()
│       │                     #   - parseGdeltDate()
│       │                     #   - stripHtml()
│       │                     #   - logger
│       │
│       └── config.ts         # Configuration
│                             #   - config object
│                             #   - ALERT_KEYWORDS
│                             #   - REGION_KEYWORDS
│                             #   - TOPIC_KEYWORDS
│                             #   - FEEDS
│                             #   - INTEL_SOURCES
│                             #   - containsAlertKeyword()
│                             #   - detectRegion()
│                             #   - detectTopics()
│                             #   - extractTickers()
│
├── tests/
│   ├── parsers.test.ts       # Parser unit tests
│   └── connectors.test.ts    # Connector tests (mocked)
│
├── output/                   # Generated output files
│
├── run_demo.ts               # Demo script
├── package.json
├── tsconfig.json
├── .env.example
├── README.md
├── ARCHITECTURE.md
└── inventory.md
```

## Key Design Decisions

### 1. Normalized Schema

All news items are transformed to a consistent `NormalizedNewsItem` schema regardless of source. This enables:
- Uniform filtering and deduplication
- Source-agnostic storage
- Consistent downstream processing

### 2. Connector Pattern

Each data source has its own connector module that:
- Handles source-specific API details
- Transforms raw data to normalized format
- Manages timeouts and error handling
- Is independently testable

### 3. Pipeline Architecture

The pipeline pattern provides:
- Clear separation of concerns (fetch → parse → filter → dedup → store)
- Easy to add new stages (e.g., summarization, sentiment)
- Configurable via options object
- Statistics and error collection

### 4. Storage Adapters

The `StorageAdapter` interface allows:
- Swappable storage backends (JSONL, SQLite, Redis, etc.)
- Consistent API for all storage types
- Easy testing with mock adapters

### 5. Configuration-Driven

All configuration is:
- Centralized in `config.ts`
- Overridable via environment variables
- Has sensible defaults
- Documented in `.env.example`

## Extension Points

### Adding a New Connector

```typescript
// src/connectors/twitter.ts
export async function fetchTwitterFeed(
  handle: string
): Promise<NormalizedNewsItem[]> {
  // 1. Fetch from Twitter API
  // 2. Transform to NormalizedNewsItem[]
  // 3. Return items
}
```

### Adding a New Filter

```typescript
// In pipeline/index.ts or custom
export function filterBySentiment(
  items: NormalizedNewsItem[],
  sentiment: 'positive' | 'negative' | 'neutral'
): NormalizedNewsItem[] {
  return items.filter(item =>
    item.metadata.sentiment === sentiment
  );
}
```

### Adding a New Storage Backend

```typescript
// src/storage/redis.ts
export class RedisStorage implements StorageAdapter {
  async save(items: NormalizedNewsItem[]): Promise<void> { ... }
  async load(): Promise<NormalizedNewsItem[]> { ... }
  async clear(): Promise<void> { ... }
}
```

## Performance Considerations

1. **Rate Limiting**: Built-in delays between requests (`DELAY_BETWEEN_REQUESTS`)
2. **Parallel Fetching**: Connectors can be run in parallel if needed
3. **Deduplication**: Hash-based O(n) deduplication
4. **Streaming**: For large datasets, consider streaming parsers/writers
5. **Caching**: Add Redis/memory cache for frequently accessed data

## Security Considerations

1. **No Secrets in Code**: All API keys via environment variables
2. **Input Sanitization**: HTML stripping prevents XSS in stored content
3. **URL Validation**: Domain extraction validates URLs
4. **CORS Proxy**: Use trusted proxies or deploy your own
