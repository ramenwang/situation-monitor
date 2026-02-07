# Situation Monitor

A real-time global intelligence and news monitoring dashboard that aggregates data from multiple sources to provide situational awareness across geopolitics, markets, technology, and defense topics.

**Live Demo**: [https://hipcityreg-situation-monitor.vercel.app/](https://hipcityreg-situation-monitor.vercel.app/)

## Features

### Multi-Category News Aggregation
- **6 News Categories**: Politics, Tech, Finance, Government, AI, and Intel
- **30+ RSS Feeds** plus GDELT API integration
- **Automatic Alert Keywords**: War, nuclear, sanctions, coup, and 18 more
- **Region Detection**: EUROPE, MENA, APAC, AMERICAS, AFRICA
- **Topic Classification**: CYBER, NUCLEAR, CONFLICT, INTEL, DEFENSE, DIPLO

### Intelligence Analysis Engine

**Correlation Analysis**
- Detects 20+ correlation topics across news sources
- Tracks emerging patterns (3+ mentions = emerging, 8+ = high)
- Momentum signals (rising/surging topics over 10-minute windows)
- Cross-source correlations from 3+ different sources

**Narrative Tracking**
- Monitors fringe-to-mainstream narrative progression
- Source classification: fringe, alternative, mainstream
- Detects disinformation patterns
- 15+ narrative patterns configured

**Main Character Analysis**
- Identifies most mentioned persons in news
- Calculates dominance score with top 10 ranking

### Market Intelligence
- **Indices**: Dow, S&P 500, NASDAQ, Russell 2000
- **Sectors**: 12 sector ETFs with heatmap visualization
- **Commodities**: VIX, Gold, Oil, Natural Gas, Silver, Copper
- **Crypto**: Bitcoin, Ethereum, Solana via CoinGecko
- **Federal Reserve**: Balance sheet and economic data from FRED

### Geopolitical Monitoring

**Interactive Global Map** (D3.js)
- 15+ critical hotspots with threat levels
- Conflict zones: Ukraine, Taiwan, Gaza, South China Sea
- Strategic chokepoints: Strait of Hormuz, Panama Canal, Suez Canal
- 20+ undersea cable landing sites
- Nuclear facilities and military bases
- Live weather from Open-Meteo API

**Situation Panels**
- Venezuela Watch
- Greenland Watch
- Iran Crisis Monitor

### Specialized Panels
- **Intel Feed**: 12+ specialized sources (CSIS, Brookings, CFR, Defense One, etc.)
- **World Leaders**: Tracking 20+ world leaders
- **Polymarket**: Prediction markets on major events
- **Whale Watch**: Large cryptocurrency transactions
- **Government Contracts**: DoD, NASA, DHS contracts
- **Layoffs Tracker**: Tech layoff announcements
- **Custom Monitors**: User-defined keyword monitoring

## Technology Stack

| Category | Technology |
|----------|------------|
| Framework | SvelteKit 2.0 + Svelte 5 |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS |
| Visualization | D3.js + TopoJSON |
| Testing | Vitest + Playwright |
| Deployment | Vercel (static) |
| Build | Vite 6.0 |

## Getting Started

### Prerequisites
- Node.js 18+
- npm or pnpm

### Installation

```bash
# Clone the repository
git clone https://github.com/hipcityreg/situation-monitor.git
cd situation-monitor

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Environment Variables (Optional)

Create a `.env` file for enhanced functionality:

```env
# Market data from Finnhub (free tier: 60 calls/min)
# Get key at: https://finnhub.io/
VITE_FINNHUB_API_KEY=your_finnhub_key

# Federal Reserve economic data
# Get key at: https://fred.stlouisfed.org/docs/api/
VITE_FRED_API_KEY=your_fred_key
```

The app works without these keys but market and Fed data panels will show empty states.

## Available Scripts

```bash
npm run dev          # Start dev server (localhost:5173)
npm run build        # Build to /build directory
npm run preview      # Preview production build (localhost:4173)
npm run check        # TypeScript type checking
npm run check:watch  # Type checking in watch mode
npm run test         # Run Vitest in watch mode
npm run test:unit    # Run unit tests once
npm run test:e2e     # Run Playwright E2E tests
npm run lint         # ESLint + Prettier check
npm run format       # Auto-format with Prettier
```

## Project Structure

```
src/
├── lib/
│   ├── analysis/       # Correlation, narrative, main-character detection
│   ├── api/            # Data fetching (GDELT, RSS, markets, FRED)
│   ├── components/
│   │   ├── layout/     # Header, Dashboard, grid layout
│   │   ├── panels/     # 19 panel components
│   │   ├── modals/     # Settings, monitor forms, onboarding
│   │   └── common/     # Shared components
│   ├── config/         # Feeds, keywords, hotspots, analysis patterns
│   ├── services/       # CacheManager, CircuitBreaker, ServiceClient
│   ├── stores/         # Svelte stores for state management
│   ├── types/          # TypeScript interfaces
│   └── utils/          # Formatting utilities
├── routes/
│   ├── +layout.svelte
│   └── +page.svelte    # Main dashboard
└── app.css             # Global styles
```

### Path Aliases

```typescript
$lib        → src/lib
$components → src/lib/components
$stores     → src/lib/stores
$services   → src/lib/services
$config     → src/lib/config
$types      → src/lib/types
```

## Architecture

### Service Resilience Layer

All HTTP requests go through `ServiceClient` which integrates:
- **CacheManager**: Per-service caching with TTL and localStorage fallback
- **CircuitBreaker**: Prevents cascading failures
- **RequestDeduplicator**: Prevents concurrent duplicate requests

### Multi-Stage Refresh

Data fetches happen in 3 stages with staggered delays to prevent UI blocking:
1. **Critical (0ms)**: News, markets, alerts
2. **Secondary (2s)**: Crypto, commodities, intel
3. **Tertiary (4s)**: Contracts, whales, layoffs, polymarket

### Configuration-Driven Design

All business logic data is centralized in `src/lib/config/`:
- `feeds.ts` - 30+ RSS sources across 6 categories
- `keywords.ts` - Alert keywords, region/topic detection
- `analysis.ts` - Correlation topics and narrative patterns
- `panels.ts` - Panel registry with display order
- `map.ts` - Geopolitical hotspots, conflict zones, strategic locations
- `markets.ts` - Sectors, commodities, indices, crypto assets

## Data Sources

| Data Type | Source | Notes |
|-----------|--------|-------|
| News | GDELT + RSS | 30+ feeds across 6 categories |
| Markets | Finnhub | Stocks, indices, ETFs, commodities |
| Crypto | CoinGecko | BTC, ETH, SOL prices |
| Fed Data | FRED API | Economic indicators |
| Weather | Open-Meteo | Conditions at map hotspots |
| Map | TopoJSON | World map topology |

## Onboarding Presets

The app includes 6 predefined dashboard configurations:

- **News Junkie**: Politics, tech, finance, gov, AI, map
- **Trader**: Markets, crypto, commodities, polymarket, whales
- **Geopolitics Watcher**: Map, intel, leaders, situation panels
- **Intelligence Analyst**: Deep analysis panels
- **Minimal**: Just map, politics, markets
- **Everything**: All 25 panels enabled

## Testing

```bash
# Unit tests (Vitest)
npm run test        # Watch mode
npm run test:unit   # Single run

# E2E tests (Playwright)
npm run preview &   # Start preview server first
npm run test:e2e    # Run E2E tests
```

## Deployment

The app is deployed as a static site:

```bash
# Build for production
npm run build

# Preview the build
npm run preview
```

**Deployment targets**:
- **Vercel** (primary): Automatic deploys from main branch
- **GitHub Pages**: Redirects to Vercel

## Contributing

1. Create a new branch for your feature
2. Make changes and add tests
3. Run `npm run lint` and `npm run check`
4. Submit a pull request

## License

MIT
