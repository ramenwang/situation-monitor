# Migration Inventory

This document lists all migrated components from the original `situation-monitor` codebase.

## Migrated Components

| Original Path | Migrated Path | What It Does | Dependencies |
|--------------|---------------|--------------|--------------|
| `src/lib/api/news.ts` | `src/connectors/gdelt.ts` | Fetches news from GDELT API | fetch, config |
| `src/lib/config/feeds.ts` | `src/utils/config.ts` (FEEDS) | RSS feed URL configuration | - |
| `src/lib/config/keywords.ts` | `src/utils/config.ts` | Alert keywords, region/topic detection | - |
| `src/lib/config/api.ts` | `src/utils/config.ts` | API configuration, logging | env vars |
| `src/lib/services/client.ts` | Simplified in connectors | HTTP client with retry | fetch |
| `src/lib/services/cache.ts` | (Not migrated - see notes) | Two-tier caching | localStorage |
| `src/lib/services/circuit-breaker.ts` | (Simplified) | Circuit breaker pattern | - |
| `src/lib/services/deduplicator.ts` | `src/pipeline/index.ts` | Request deduplication | - |
| `src/lib/types/index.ts` | `src/types/index.ts` | TypeScript interfaces | - |
| `src/lib/utils/format.ts` | `src/utils/index.ts` | Formatting utilities | - |

## New Components (Created for Migration)

| Path | What It Does | Dependencies |
|------|--------------|--------------|
| `src/connectors/rss.ts` | RSS/Atom feed fetching and parsing | fetch |
| `src/parsers/index.ts` | Text cleaning, normalization, entity extraction | - |
| `src/pipeline/index.ts` | Orchestrates fetch→parse→filter→dedup→store | connectors, parsers, storage |
| `src/storage/jsonl.ts` | JSONL file output adapter | fs |
| `src/storage/sqlite.ts` | SQLite database adapter | better-sqlite3 (optional) |

## Configuration Required

| Variable | Required | Description |
|----------|----------|-------------|
| `CORS_PROXY_PRIMARY` | For RSS | CORS proxy URL for RSS feeds |
| `CORS_PROXY_FALLBACK` | No | Fallback CORS proxy |
| `FINNHUB_API_KEY` | For markets | Finnhub API key (free tier available) |
| `FRED_API_KEY` | For Fed data | FRED API key (free tier available) |
| `DEBUG` | No | Enable debug logging |
| `REQUEST_TIMEOUT` | No | Request timeout in ms (default: 15000) |
| `OUTPUT_DIR` | No | Output directory (default: ./output) |

## Not Migrated

| Component | Reason |
|-----------|--------|
| `src/lib/analysis/correlation.ts` | Too coupled to UI display logic, specific to their dashboard |
| `src/lib/analysis/narrative.ts` | Business logic specific to their narrative tracking use case |
| `src/lib/analysis/main-character.ts` | Specific to their "main character" analysis feature |
| `src/lib/stores/*.ts` | Svelte-specific state management (writable stores) |
| `src/lib/components/**` | Svelte UI components, not relevant for backend scanner |
| `src/lib/config/panels.ts` | UI panel configuration |
| `src/lib/config/presets.ts` | Dashboard presets |
| `src/lib/config/map.ts` | Geopolitical map configuration |
| `src/lib/config/leaders.ts` | World leaders tracking (mock data) |
| `src/lib/config/markets.ts` | Partial - sector/commodity lists (can add if needed) |
| `src/lib/api/markets.ts` | Partial - Finnhub integration (can add if needed) |
| `src/lib/api/fred.ts` | Fed Reserve data (can add if needed) |
| `src/lib/api/misc.ts` | Mock data for Polymarket, whales, contracts |
| `src/lib/services/cache.ts` | Uses localStorage (browser-specific), simplified for Node.js |
| `src/lib/services/registry.ts` | Service registry (simplified inline) |

## Simplifications Made

1. **Cache Layer**: The original uses a sophisticated two-tier cache (memory + localStorage). For a Node.js backend scanner, this was simplified to in-memory only. Add Redis if needed.

2. **Circuit Breaker**: Simplified - the original has a full CircuitBreakerRegistry. For the migration, basic error handling with retries is implemented.

3. **Request Deduplication**: The original deduplicator is for browser concurrent requests. In a sequential scanner, this is replaced with simpler ID-based deduplication.

4. **RSS Parsing**: Created a lightweight XML parser. For production, consider using `fast-xml-parser` or `rss-parser`.

5. **Svelte Removal**: All `$app/environment` and Svelte store dependencies removed. Pure TypeScript.

## Adding Back Features

### Markets API

To add stock/crypto price fetching:

1. Copy `src/lib/api/markets.ts` and `src/lib/config/markets.ts`
2. Remove the `$lib` path aliases
3. Add to the pipeline or use standalone

### Full Caching

To add Redis caching:

```typescript
import Redis from 'ioredis';

export class RedisCache {
  private redis: Redis;

  constructor(url: string) {
    this.redis = new Redis(url);
  }

  async get<T>(key: string): Promise<T | null> {
    const data = await this.redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  async set<T>(key: string, value: T, ttl: number): Promise<void> {
    await this.redis.set(key, JSON.stringify(value), 'PX', ttl);
  }
}
```

### Scheduling

To add periodic polling:

```typescript
import { runPipeline } from './pipeline';

async function scheduledFetch() {
  while (true) {
    await runPipeline({ storage: myStorage });
    await new Promise(r => setTimeout(r, 5 * 60 * 1000)); // 5 minutes
  }
}
```

Or use a proper scheduler like `node-cron`:

```typescript
import cron from 'node-cron';

cron.schedule('*/5 * * * *', async () => {
  await runPipeline({ storage: myStorage });
});
```
