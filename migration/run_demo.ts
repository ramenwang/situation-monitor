#!/usr/bin/env npx ts-node
/**
 * News Pipeline Demo
 *
 * This script demonstrates the full pipeline:
 * 1. Fetches news from GDELT and RSS sources
 * 2. Parses and normalizes articles
 * 3. Filters and deduplicates
 * 4. Outputs to JSONL file
 *
 * Usage:
 *   npx ts-node run_demo.ts
 *   # or
 *   npm run demo
 */

import { NewsPipeline, createJsonlStorage, logger } from './src';
import type { PipelineResult } from './src/types';

// Enable debug logging
process.env.DEBUG = 'true';

async function main(): Promise<void> {
  console.log('='.repeat(60));
  console.log('Trading News Scanner - Demo');
  console.log('='.repeat(60));
  console.log();

  // Create storage adapter
  const storage = createJsonlStorage('./migration/output');

  // Create pipeline with configuration
  const pipeline = new NewsPipeline({
    // Fetch from both GDELT and RSS
    useGdelt: true,
    useRss: true,
    useIntel: true,

    // Categories to fetch
    categories: ['finance', 'tech', 'politics'],

    // Optional filter: only trading-relevant topics
    filter: {
      // topics: ['FINANCE', 'CRYPTO', 'TECH'],
      // max_age_ms: 24 * 60 * 60 * 1000, // Last 24 hours
    },

    // Use CORS proxies for RSS (needed in browser, optional in Node)
    corsProxies: [
      'https://api.allorigins.win/raw?url=',
    ],

    // Output storage
    storage,
  });

  console.log('Starting pipeline...');
  console.log();

  try {
    const result: PipelineResult = await pipeline.run();

    // Print summary
    console.log();
    console.log('='.repeat(60));
    console.log('Pipeline Results');
    console.log('='.repeat(60));
    console.log();
    console.log(`Fetched:      ${result.stats.fetched} items`);
    console.log(`Parsed:       ${result.stats.parsed} items`);
    console.log(`Filtered:     ${result.stats.filtered} items removed`);
    console.log(`Deduplicated: ${result.stats.deduplicated} duplicates removed`);
    console.log(`Final:        ${result.items.length} items`);
    console.log(`Duration:     ${result.stats.duration_ms}ms`);
    console.log();

    if (result.errors.length > 0) {
      console.log('Errors:');
      for (const error of result.errors) {
        console.log(`  - [${error.stage}] ${error.source || ''}: ${error.message}`);
      }
      console.log();
    }

    // Print sample items
    console.log('Sample Items (first 5):');
    console.log('-'.repeat(60));

    for (const item of result.items.slice(0, 5)) {
      console.log();
      console.log(`Title:     ${item.title.slice(0, 70)}${item.title.length > 70 ? '...' : ''}`);
      console.log(`Source:    ${item.source}`);
      console.log(`Published: ${item.published_at}`);
      console.log(`Topics:    ${item.topics.join(', ') || 'none'}`);
      console.log(`Tickers:   ${item.tickers.join(', ') || 'none'}`);
      console.log(`Alert:     ${item.metadata.is_alert ? `YES (${item.metadata.alert_keyword})` : 'no'}`);
      console.log(`URL:       ${item.url}`);
    }

    console.log();
    console.log('-'.repeat(60));
    console.log(`Output saved to: ${storage.getFilePath()}`);
    console.log();

    // Print alert items if any
    const alerts = result.items.filter((item) => item.metadata.is_alert);
    if (alerts.length > 0) {
      console.log('='.repeat(60));
      console.log(`ALERTS (${alerts.length} items with alert keywords)`);
      console.log('='.repeat(60));

      for (const alert of alerts.slice(0, 10)) {
        console.log(`[${alert.metadata.alert_keyword?.toUpperCase()}] ${alert.title.slice(0, 60)}`);
      }

      if (alerts.length > 10) {
        console.log(`... and ${alerts.length - 10} more alerts`);
      }
      console.log();
    }

    // Print topic distribution
    const topicCounts = new Map<string, number>();
    for (const item of result.items) {
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

    // Print source distribution
    const sourceCounts = new Map<string, number>();
    for (const item of result.items) {
      sourceCounts.set(item.source, (sourceCounts.get(item.source) || 0) + 1);
    }

    console.log('Source Distribution (top 10):');
    const sortedSources = Array.from(sourceCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    for (const [source, count] of sortedSources) {
      console.log(`  ${source.padEnd(25)} ${count}`);
    }
    console.log();

  } catch (error) {
    console.error('Pipeline failed:', error);
    process.exit(1);
  }
}

// Run the demo
main().catch(console.error);
