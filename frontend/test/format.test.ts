import { describe, expect, it } from 'vitest';
import { formatNumber } from '../src/utils';
import { FrontendLocaleData, HomeAssistant } from '../src/types';

/**
 * Values were interpolated into the template straight from the state, so every
 * user got the JavaScript spelling - "12.5" - beside a Home Assistant interface
 * that had been showing them "12,5" everywhere else.
 */
const hass = (locale: Partial<FrontendLocaleData>, language = 'en'): HomeAssistant =>
  ({
    language,
    locale: { language, number_format: 'system', time_format: '24', ...locale },
  }) as unknown as HomeAssistant;

describe('formatNumber', () => {
  it('follows the comma_decimal setting', () => {
    expect(formatNumber('1234.5', hass({ number_format: 'comma_decimal' }))).toBe('1,234.5');
  });

  it('follows the decimal_comma setting', () => {
    expect(formatNumber('1234.5', hass({ number_format: 'decimal_comma' }))).toBe('1.234,5');
  });

  it('follows the space_comma setting', () => {
    // The group separator is a non-breaking space of one kind or another, so
    // the decimal mark is what this pins.
    expect(formatNumber('1234.5', hass({ number_format: 'space_comma' }))).toContain(',5');
  });

  it('follows the number format rather than the interface language', () => {
    // A German user reading an English interface still wants "12,5".
    expect(formatNumber('12.5', hass({ number_format: 'decimal_comma' }, 'en'))).toBe('12,5');
  });

  it('leaves the digits alone when the user asked for no formatting', () => {
    expect(formatNumber('1234.5', hass({ number_format: 'none' }))).toBe('1234.5');
  });

  it('passes non-numeric states straight through', () => {
    // Condition sensors carry bergfex's free text, and "NaN" would be worse
    // than the text itself.
    expect(formatNumber('unknown', hass({ number_format: 'decimal_comma' }))).toBe('unknown');
    expect(formatNumber('sulzig', hass({ number_format: 'decimal_comma' }))).toBe('sulzig');
  });

  it('renders nothing for an absent value', () => {
    expect(formatNumber(undefined, hass({}))).toBe('');
    expect(formatNumber(null, hass({}))).toBe('');
    expect(formatNumber('', hass({}))).toBe('');
  });

  it('does not throw before hass has arrived', () => {
    expect(() => formatNumber('12.5', undefined)).not.toThrow();
    expect(formatNumber('12.5', undefined)).toContain('12');
  });

  it('takes numbers as well as states', () => {
    expect(formatNumber(12.5, hass({ number_format: 'decimal_comma' }))).toBe('12,5');
  });
});
