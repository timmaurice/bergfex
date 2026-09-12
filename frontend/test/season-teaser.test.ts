/**
 * The season teaser's date.
 *
 * It was formatted with `{ day: '2-digit', month: '2-digit' }`, so a season
 * starting on 12 April read "ab 12/04" - which is the 4th of December to most
 * of the world. A season start is precisely the value nobody can infer from
 * context, so the month is named: `month: 'short'` is the fix.
 *
 * The source now reads `hass.locale.language` in preference to `hass.language`.
 * That is cosmetic - both are the same profile language - and the setting that
 * really decides date format, `locale.date_format`, is not read by this card at
 * all. The test below pins the preference order anyway so it cannot silently
 * regress to the interface language.
 */
import { describe, expect, it, vi } from 'vitest';

import '../src/bergfex-card';
import type { BergfexCard } from '../src/bergfex-card';
import type { FrontendLocaleData, HomeAssistant } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

const card = (locale: string, language: string): BergfexCard => {
  const element = document.createElement('bergfex-card') as BergfexCard;
  element.hass = {
    localize: (key: string) => key,
    language,
    locale: { language: locale, number_format: 'comma_decimal', time_format: '24' } as FrontendLocaleData,
    states: {},
    entities: {},
    devices: {},
  } as unknown as HomeAssistant;
  return element;
};

/** The teaser, with the date the mocked localize would otherwise swallow. */
const teaserDate = (element: BergfexCard, start: string, end: string): string | undefined => {
  const teaser = (
    element as unknown as {
      _winterTeaser(attrs: Record<string, unknown>): string | undefined;
    }
  )._winterTeaser({ winter_season_start: start, winter_season_end: end });
  return teaser;
};

// Far enough out that the teaser treats the date as definite rather than as
// last season's leftover.
const nextApril = () => {
  const year = new Date().getFullYear() + (new Date().getMonth() >= 3 ? 1 : 0);
  return { start: `${year}-04-12`, end: `${year}-04-30` };
};

describe('season teaser date', () => {
  it('names the month rather than numbering it', () => {
    const { start, end } = nextApril();
    const teaser = teaserDate(card('en', 'en'), start, end) ?? '';

    // The whole point: "12/04" is ambiguous, "Apr" cannot be misread.
    expect(teaser).not.toContain('/');
    expect(teaser.toLowerCase()).toContain('apr');
  });

  it('follows the locale, not the interface language', () => {
    const { start, end } = nextApril();
    // A user reading an English interface with their locale set to German.
    const teaser = teaserDate(card('de', 'en'), start, end) ?? '';

    expect(teaser.toLowerCase()).toContain('apr');
    // German writes the day first and marks it with a full stop.
    expect(teaser).toContain('12.');
  });

  it('still gives up on a date it cannot read', () => {
    expect(teaserDate(card('en', 'en'), 'not-a-date', 'not-a-date')).toBeUndefined();
  });
});
