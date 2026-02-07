#!/usr/bin/env node
/**
 * Standalone News Pipeline Demo
 *
 * This demo runs without any npm dependencies - uses only Node.js built-ins.
 * Works with Node 18+ (native fetch support).
 *
 * Usage:
 *   node demo.mjs
 */

import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
  corsProxy: 'https://api.allorigins.win/raw?url=',
  gdeltBaseUrl: 'https://api.gdeltproject.org',
  timeout: 15000,
  delayBetweenRequests: 500,
};

const ALERT_KEYWORDS = [
  'war', 'invasion', 'military', 'nuclear', 'sanctions', 'missile', 'attack',
  'troops', 'conflict', 'strike', 'bomb', 'casualties', 'ceasefire', 'treaty',
  'nato', 'coup', 'martial law', 'emergency', 'assassination', 'terrorist'
];

const TOPIC_KEYWORDS = {
  FINANCE: ['fed', 'interest rate', 'inflation', 'gdp', 'recession', 'rally', 'crash', 'stock', 'market'],
  CRYPTO: ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi'],
  TECH: ['ai', 'artificial intelligence', 'machine learning', 'startup', 'ipo'],
  CYBER: ['cyber', 'hack', 'ransomware', 'malware', 'breach'],
  CONFLICT: ['war', 'military', 'troops', 'invasion', 'strike', 'missile'],
};

const GDELT_QUERIES = {
  finance: '(finance OR "stock market" OR economy OR banking)',
  tech: '(technology OR software OR startup OR AI)',
  politics: '(politics OR government OR election OR congress)',
};

// ============================================================================
// Utilities
// ============================================================================

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

function generateId(url, source) {
  return `${hashCode(source)}-${hashCode(url)}`;
}

function parseGdeltDate(dateStr) {
  if (!dateStr) return new Date().toISOString();
  const match = dateStr.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/);
  if (match) {
    const [, year, month, day, hour, min, sec] = match;
    return `${year}-${month}-${day}T${hour}:${min}:${sec}Z`;
  }
  return new Date(dateStr).toISOString();
}

function detectAlertKeyword(text) {
  const lower = text.toLowerCase();
  for (const kw of ALERT_KEYWORDS) {
    if (lower.includes(kw)) return kw;
  }
  return null;
}

function detectTopics(text) {
  const lower = text.toLowerCase();
  const topics = [];
  for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
    if (keywords.some(k => lower.includes(k))) {
      topics.push(topic);
    }
  }
  return topics;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// GDELT Connector
// ============================================================================

async function fetchGdelt(category) {
  const query = GDELT_QUERIES[category];
  if (!query) return [];

  const fullQuery = `${query} sourcelang:english`;
  const url = `${CONFIG.gdeltBaseUrl}/api/v2/doc/doc?query=${encodeURIComponent(fullQuery)}&timespan=7d&mode=artlist&maxrecords=15&format=json&sort=date`;

  console.log(`  Fetching GDELT ${category}...`);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      console.log(`  GDELT ${category}: HTTP ${response.status}`);
      return [];
    }

    const data = await response.json();
    if (!data?.articles) return [];

    console.log(`  GDELT ${category}: ${data.articles.length} articles`);

    return data.articles.map(article => {
      const alertKw = detectAlertKeyword(article.title || '');
      return {
        id: generateId(article.url, `gdelt-${category}`),
        source: article.domain || 'GDELT',
        url: article.url,
        title: article.title || '',
        published_at: parseGdeltDate(article.seendate),
        fetched_at: new Date().toISOString(),
        authors: [],
        summary: '',
        content_text: '',
        tickers: [],
        topics: detectTopics(article.title || ''),
        language: 'en',
        metadata: {
          category,
          is_alert: !!alertKw,
          alert_keyword: alertKw,
        }
      };
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log(`  GDELT ${category}: Timeout`);
    } else {
      console.log(`  GDELT ${category}: ${error.message}`);
    }
    return [];
  }
}

// ============================================================================
// Deduplication
// ============================================================================

function deduplicateItems(items) {
  const seen = new Map();
  const titleHashes = new Set();

  for (const item of items) {
    if (seen.has(item.id)) continue;

    const normalizedTitle = item.title.toLowerCase().replace(/[^a-z0-9]/g, '');
    const titleHash = hashCode(normalizedTitle);

    if (titleHashes.has(titleHash)) continue;

    seen.set(item.id, item);
    titleHashes.add(titleHash);
  }

  return Array.from(seen.values());
}

// ============================================================================
// Main Pipeline
// ============================================================================

async function runPipeline() {
  console.log('='.repeat(60));
  console.log('Trading News Scanner - Demo');
  console.log('='.repeat(60));
  console.log();

  const startTime = Date.now();
  let allItems = [];

  // Fetch from GDELT
  console.log('Fetching news from GDELT...');
  for (const category of ['finance', 'tech', 'politics']) {
    const items = await fetchGdelt(category);
    allItems.push(...items);
    await delay(CONFIG.delayBetweenRequests);
  }

  console.log();
  console.log(`Total fetched: ${allItems.length} items`);

  // Deduplicate
  const beforeDedup = allItems.length;
  allItems = deduplicateItems(allItems);
  console.log(`After dedup: ${allItems.length} items (removed ${beforeDedup - allItems.length})`);

  // Sort by date
  allItems.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));

  const duration = Date.now() - startTime;
  console.log(`Duration: ${duration}ms`);
  console.log();

  // Save output
  const outputDir = join(__dirname, 'output');
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const outputPath = join(outputDir, `news-${timestamp}.jsonl`);
  const content = allItems.map(item => JSON.stringify(item)).join('\n') + '\n';
  writeFileSync(outputPath, content, 'utf8');
  console.log(`Output saved to: ${outputPath}`);
  console.log();

  // Print sample
  console.log('Sample Items (first 5):');
  console.log('-'.repeat(60));
  for (const item of allItems.slice(0, 5)) {
    console.log();
    console.log(`Title:     ${item.title.slice(0, 70)}${item.title.length > 70 ? '...' : ''}`);
    console.log(`Source:    ${item.source}`);
    console.log(`Topics:    ${item.topics.join(', ') || 'none'}`);
    console.log(`Alert:     ${item.metadata.is_alert ? `YES (${item.metadata.alert_keyword})` : 'no'}`);
  }
  console.log();

  // Print alerts
  const alerts = allItems.filter(item => item.metadata.is_alert);
  if (alerts.length > 0) {
    console.log('='.repeat(60));
    console.log(`ALERTS (${alerts.length} items)`);
    console.log('='.repeat(60));
    for (const alert of alerts.slice(0, 10)) {
      console.log(`[${alert.metadata.alert_keyword?.toUpperCase()}] ${alert.title.slice(0, 55)}...`);
    }
    console.log();
  }

  // Print topic distribution
  const topicCounts = new Map();
  for (const item of allItems) {
    for (const topic of item.topics) {
      topicCounts.set(topic, (topicCounts.get(topic) || 0) + 1);
    }
  }

  if (topicCounts.size > 0) {
    console.log('Topic Distribution:');
    const sorted = Array.from(topicCounts.entries()).sort((a, b) => b[1] - a[1]);
    for (const [topic, count] of sorted) {
      const bar = '#'.repeat(Math.min(count, 30));
      console.log(`  ${topic.padEnd(12)} ${count.toString().padStart(3)} ${bar}`);
    }
    console.log();
  }

  console.log('Done!');
}

// Run
runPipeline().catch(console.error);
