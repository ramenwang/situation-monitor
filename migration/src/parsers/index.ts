/**
 * Parsers for text extraction and normalization
 */

import type { NormalizedNewsItem } from '../types';
import { stripHtml, extractDomain } from '../utils';
import { extractTickers, detectTopics, detectRegion, containsAlertKeyword } from '../utils/config';

/**
 * Clean and normalize article text
 */
export function cleanText(text: string): string {
  if (!text) return '';

  // Strip HTML
  let clean = stripHtml(text);

  // Remove common RSS artifacts
  clean = clean
    .replace(/\[…\]/g, '...')
    .replace(/\[\.\.\.\]/g, '...')
    .replace(/Continue reading\.\.\.$/i, '')
    .replace(/Read more\.\.\.$/i, '')
    .replace(/\s+/g, ' ')
    .trim();

  return clean;
}

/**
 * Extract summary from content
 * Takes first N sentences or characters
 */
export function extractSummary(content: string, maxLength = 300): string {
  if (!content) return '';

  const clean = cleanText(content);

  // Try to break at sentence boundary
  if (clean.length <= maxLength) return clean;

  // Find last sentence boundary before maxLength
  const truncated = clean.slice(0, maxLength);
  const lastPeriod = truncated.lastIndexOf('.');
  const lastQuestion = truncated.lastIndexOf('?');
  const lastExclaim = truncated.lastIndexOf('!');

  const boundary = Math.max(lastPeriod, lastQuestion, lastExclaim);

  if (boundary > maxLength * 0.5) {
    return clean.slice(0, boundary + 1);
  }

  // Fall back to word boundary
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > maxLength * 0.7) {
    return clean.slice(0, lastSpace) + '...';
  }

  return truncated + '...';
}

/**
 * Normalize a news item - ensure all fields are properly set
 */
export function normalizeItem(item: Partial<NormalizedNewsItem>): NormalizedNewsItem {
  const title = cleanText(item.title || '');
  const summary = item.summary ? cleanText(item.summary) : '';
  const content = item.content_text ? cleanText(item.content_text) : '';

  // Combine all text for analysis
  const fullText = `${title} ${summary} ${content}`;

  // Extract/detect if not already set
  const topics = item.topics?.length ? item.topics : detectTopics(fullText);
  const tickers = item.tickers?.length ? item.tickers : extractTickers(fullText);
  const region = item.metadata?.region || detectRegion(fullText);
  const alert = item.metadata?.is_alert !== undefined
    ? { is_alert: item.metadata.is_alert, keyword: item.metadata.alert_keyword }
    : containsAlertKeyword(title);

  return {
    id: item.id || '',
    source: item.source || extractDomain(item.url || ''),
    url: item.url || '',
    title,
    published_at: item.published_at || new Date().toISOString(),
    fetched_at: item.fetched_at || new Date().toISOString(),
    authors: item.authors || [],
    summary: summary || extractSummary(content),
    content_text: content,
    tickers,
    topics,
    language: item.language || 'en',
    metadata: {
      ...item.metadata,
      is_alert: alert.is_alert,
      alert_keyword: alert.keyword,
      region: region ?? undefined,
    },
  };
}

/**
 * Parse and normalize multiple items
 */
export function parseItems(items: Partial<NormalizedNewsItem>[]): NormalizedNewsItem[] {
  return items.map(normalizeItem);
}

/**
 * Extract authors from various formats
 */
export function parseAuthors(authorField: string | string[] | undefined): string[] {
  if (!authorField) return [];

  if (Array.isArray(authorField)) {
    return authorField.map((a) => cleanText(a)).filter(Boolean);
  }

  // Handle common formats: "By John Doe", "John Doe and Jane Smith", etc.
  let text = cleanText(authorField);

  // Remove "By " prefix
  text = text.replace(/^By\s+/i, '');

  // Split on " and " or ", "
  const authors = text
    .split(/(?:\s+and\s+|,\s*)/i)
    .map((a) => a.trim())
    .filter(Boolean);

  return authors;
}

/**
 * Parse date from various formats
 */
export function parseDate(dateStr: string | undefined): string {
  if (!dateStr) return new Date().toISOString();

  try {
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      return date.toISOString();
    }
  } catch {
    // Fall through
  }

  // Try common formats
  const formats = [
    // RFC 2822: "Wed, 02 Oct 2002 15:00:00 +0200"
    /^[A-Za-z]{3},?\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}/,
    // ISO: "2023-12-01T12:00:00Z"
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/,
    // GDELT: "20231201T120000Z"
    /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/,
  ];

  for (const format of formats) {
    const match = dateStr.match(format);
    if (match) {
      try {
        // GDELT format needs conversion
        if (match.length === 7) {
          const [, year, month, day, hour, min, sec] = match;
          return new Date(`${year}-${month}-${day}T${hour}:${min}:${sec}Z`).toISOString();
        }
        return new Date(dateStr).toISOString();
      } catch {
        continue;
      }
    }
  }

  return new Date().toISOString();
}
