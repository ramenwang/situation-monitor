/**
 * Utility functions for the news pipeline
 */

import { config } from './config';

/**
 * Generate a stable hash from a string (for ID generation)
 */
export function hashCode(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36);
}

/**
 * Generate a unique ID from URL and source
 */
export function generateId(url: string, source: string): string {
  const urlHash = hashCode(url);
  const sourceHash = hashCode(source);
  return `${sourceHash}-${urlHash}`;
}

/**
 * Parse GDELT date format (20251202T224500Z) to ISO8601
 */
export function parseGdeltDate(dateStr: string): string {
  if (!dateStr) return new Date().toISOString();

  const match = dateStr.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/);
  if (match) {
    const [, year, month, day, hour, min, sec] = match;
    return `${year}-${month}-${day}T${hour}:${min}:${sec}Z`;
  }

  // Try standard parsing
  try {
    return new Date(dateStr).toISOString();
  } catch {
    return new Date().toISOString();
  }
}

/**
 * Parse RFC 2822 date (common in RSS) to ISO8601
 */
export function parseRssDate(dateStr: string): string {
  if (!dateStr) return new Date().toISOString();

  try {
    return new Date(dateStr).toISOString();
  } catch {
    return new Date().toISOString();
  }
}

/**
 * Get current ISO8601 timestamp
 */
export function nowISO(): string {
  return new Date().toISOString();
}

/**
 * Delay helper
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate exponential backoff delay with jitter
 */
export function getBackoffDelay(attempt: number, baseMs = 1000, maxMs = 10000): number {
  const baseDelay = Math.pow(2, attempt) * baseMs;
  const jitter = Math.random() * 500;
  return Math.min(baseDelay + jitter, maxMs);
}

/**
 * Clean HTML from text
 */
export function stripHtml(html: string): string {
  if (!html) return '';
  // Remove HTML tags
  let text = html.replace(/<[^>]*>/g, ' ');
  // Decode common HTML entities
  text = text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
  // Normalize whitespace
  text = text.replace(/\s+/g, ' ').trim();
  return text;
}

/**
 * Truncate text to max length
 */
export function truncate(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Extract domain from URL
 */
export function extractDomain(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

/**
 * Conditional logger
 */
export const logger = {
  debug: (...args: unknown[]) => {
    if (config.debug) {
      console.log('[DEBUG]', ...args);
    }
  },
  info: (...args: unknown[]) => {
    console.log('[INFO]', ...args);
  },
  warn: (...args: unknown[]) => {
    console.warn('[WARN]', ...args);
  },
  error: (...args: unknown[]) => {
    console.error('[ERROR]', ...args);
  },
};
