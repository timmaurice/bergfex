/**
 * What the card does when the user's locale changes, and how it prints a
 * forecast date.
 *
 * `shouldUpdate` compared only `hass.language`, while the season teaser and the
 * forecast date format against `hass.locale` and every number goes through
 * `locale.number_format`. A locale-only profile change therefore left the card
 * showing the old format until something unrelated happened to re-render it.
 */
import { describe, expect, it, vi } from 'vitest';

import '../src/bergfex-card';
import type { BergfexCard } from '../src/bergfex-card';
import type { BergfexCardConfig, FrontendLocaleData, HomeAssistant } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

vi.mock('../src/localize.ts', () => ({
  localize: (_hass: unknown, key: string) => key,
}));

const hass = (locale: Partial<FrontendLocaleData>, language = 'en'): HomeAssistant =>
  ({
    localize: (key: string) => key,
    language,
    locale: { language, number_format: 'comma_decimal', time_format: '24', ...locale },
    states: {},
    entities: {},
    devices: {},
    callWS: vi.fn(),
  }) as unknown as HomeAssistant;

/** A card with `hass` already set, and the map lit would hand `shouldUpdate`. */
const cardWith = (before: HomeAssistant, after: HomeAssistant) => {
  const element = document.createElement('bergfex-card') as BergfexCard;
  element.hass = before;
  element.setConfig({ type: 'custom:bergfex-card', resorts: ['device-1'] } as BergfexCardConfig);
  element.hass = after;
  const internals = element as unknown as {
    shouldUpdate(changed: Map<string | number | symbol, unknown>): boolean;
    _formatForecastDate(dayOffset: number): string;
  };
  return {
    shouldUpdate: () => internals.shouldUpdate(new Map<string | number | symbol, unknown>([['hass', before]])),
    forecastDate: (offset: number) => internals._formatForecastDate(offset),
  };
};

describe('shouldUpdate', () => {
  it('re-renders when only the locale language changed', () => {
    const before = hass({ language: 'en' });
    const after = hass({ language: 'de' });

    expect(cardWith(before, after).shouldUpdate()).toBe(true);
  });

  it('re-renders when only the number format changed', () => {
    // Every value in the card goes through formatNumber, so "12.5" would
    // otherwise stay put beside an interface that now says "12,5".
    const before = hass({ number_format: 'comma_decimal' });
    const after = hass({ number_format: 'decimal_comma' });

    expect(cardWith(before, after).shouldUpdate()).toBe(true);
  });

  it('re-renders when only the time format changed', () => {
    const before = hass({ time_format: '24' });
    const after = hass({ time_format: '12' });

    expect(cardWith(before, after).shouldUpdate()).toBe(true);
  });

  it('still re-renders on the interface language alone', () => {
    const before = hass({}, 'en');
    const after = hass({ language: 'en' }, 'de');

    expect(cardWith(before, after).shouldUpdate()).toBe(true);
  });

  it('does not re-render when nothing the card reads changed', () => {
    const before = hass({});
    const after = hass({});

    expect(cardWith(before, after).shouldUpdate()).toBe(false);
  });
});

describe('forecast date', () => {
  it('names the month, the way the season teaser does', () => {
    // "Fr, 12/04" is the 12th of April or the 4th of December depending on the
    // reader, and the two dates in one card should not disagree on the format.
    const card = cardWith(hass({ language: 'en' }), hass({ language: 'en' }));
    const formatted = card.forecastDate(3);

    expect(formatted).not.toMatch(/\d\d[./-]\d\d/);
    expect(formatted).toMatch(/[A-Za-z]{3}/);
  });

  it('follows the locale rather than the interface language', () => {
    const card = cardWith(hass({ language: 'de' }, 'en'), hass({ language: 'de' }, 'en'));

    // German abbreviates with a trailing full stop and puts the day first.
    expect(card.forecastDate(3)).toMatch(/^[A-Za-zÄÖÜäöü]{2}\.,? \d/);
  });
});
