/**
 * Parser Tests
 */

import { describe, it, expect } from 'vitest';
import {
  cleanText,
  extractSummary,
  normalizeItem,
  parseAuthors,
  parseDate,
} from '../src/parsers';

describe('cleanText', () => {
  it('should strip HTML tags', () => {
    expect(cleanText('<p>Hello <b>World</b></p>')).toBe('Hello World');
  });

  it('should decode HTML entities', () => {
    expect(cleanText('Hello &amp; World')).toBe('Hello & World');
    expect(cleanText('&lt;script&gt;')).toBe('<script>');
    expect(cleanText('&quot;quoted&quot;')).toBe('"quoted"');
  });

  it('should normalize whitespace', () => {
    expect(cleanText('Hello   \n\t  World')).toBe('Hello World');
  });

  it('should remove RSS artifacts', () => {
    expect(cleanText('Article content […]')).toBe('Article content ...');
    expect(cleanText('Preview text Continue reading...')).toBe('Preview text');
  });

  it('should handle empty input', () => {
    expect(cleanText('')).toBe('');
    expect(cleanText(null as unknown as string)).toBe('');
    expect(cleanText(undefined as unknown as string)).toBe('');
  });
});

describe('extractSummary', () => {
  it('should return short text unchanged', () => {
    const text = 'This is a short text.';
    expect(extractSummary(text, 100)).toBe(text);
  });

  it('should truncate at sentence boundary', () => {
    const text = 'First sentence. Second sentence. Third sentence is very long and should be cut off.';
    const result = extractSummary(text, 50);
    expect(result).toBe('First sentence. Second sentence.');
  });

  it('should truncate at word boundary with ellipsis', () => {
    const text = 'This is a sentence without any periods for truncation testing purposes here';
    const result = extractSummary(text, 40);
    expect(result).toContain('...');
    expect(result.length).toBeLessThanOrEqual(43); // 40 + "..."
  });
});

describe('normalizeItem', () => {
  it('should normalize a minimal item', () => {
    const item = normalizeItem({
      id: 'test-1',
      url: 'https://example.com/article',
      title: 'Test Article',
    });

    expect(item.id).toBe('test-1');
    expect(item.url).toBe('https://example.com/article');
    expect(item.title).toBe('Test Article');
    expect(item.source).toBe('example.com');
    expect(item.authors).toEqual([]);
    expect(item.tickers).toEqual([]);
    expect(item.topics).toEqual([]);
    expect(item.language).toBe('en');
  });

  it('should detect topics from content', () => {
    const item = normalizeItem({
      id: 'test-2',
      url: 'https://example.com/article',
      title: 'Cyber attack on military base',
    });

    expect(item.topics).toContain('CYBER');
    expect(item.topics).toContain('DEFENSE');
  });

  it('should detect alert keywords', () => {
    const item = normalizeItem({
      id: 'test-3',
      url: 'https://example.com/article',
      title: 'Nuclear weapons treaty signed',
    });

    expect(item.metadata.is_alert).toBe(true);
    expect(item.metadata.alert_keyword).toBe('nuclear');
  });

  it('should preserve existing metadata', () => {
    const item = normalizeItem({
      id: 'test-4',
      url: 'https://example.com/article',
      title: 'Test',
      metadata: {
        category: 'finance',
        custom_field: 'value',
      },
    });

    expect(item.metadata.category).toBe('finance');
    expect((item.metadata as Record<string, unknown>).custom_field).toBe('value');
  });
});

describe('parseAuthors', () => {
  it('should handle string author', () => {
    expect(parseAuthors('John Doe')).toEqual(['John Doe']);
  });

  it('should handle "By" prefix', () => {
    expect(parseAuthors('By John Doe')).toEqual(['John Doe']);
  });

  it('should split multiple authors', () => {
    expect(parseAuthors('John Doe and Jane Smith')).toEqual(['John Doe', 'Jane Smith']);
    expect(parseAuthors('John Doe, Jane Smith')).toEqual(['John Doe', 'Jane Smith']);
  });

  it('should handle array input', () => {
    expect(parseAuthors(['John Doe', 'Jane Smith'])).toEqual(['John Doe', 'Jane Smith']);
  });

  it('should handle empty input', () => {
    expect(parseAuthors(undefined)).toEqual([]);
    expect(parseAuthors('')).toEqual([]);
  });
});

describe('parseDate', () => {
  it('should parse ISO 8601 dates', () => {
    const result = parseDate('2024-01-15T12:00:00Z');
    expect(result).toBe('2024-01-15T12:00:00.000Z');
  });

  it('should parse RFC 2822 dates', () => {
    const result = parseDate('Mon, 15 Jan 2024 12:00:00 +0000');
    expect(new Date(result).getFullYear()).toBe(2024);
  });

  it('should parse GDELT format dates', () => {
    const result = parseDate('20240115T120000Z');
    expect(result).toBe('2024-01-15T12:00:00.000Z');
  });

  it('should return current date for invalid input', () => {
    const result = parseDate('not a date');
    const parsed = new Date(result);
    expect(parsed.getTime()).toBeCloseTo(Date.now(), -3);
  });

  it('should handle empty input', () => {
    const result = parseDate(undefined);
    const parsed = new Date(result);
    expect(parsed.getTime()).toBeCloseTo(Date.now(), -3);
  });
});
