/**
 * The card must recognise "there is no report" in every language the
 * integration can be configured in.
 *
 * bergfex writes the phrase in the language of the page a resort was set up in,
 * and the card printed anything it did not recognise as if it were a real snow
 * condition. Seven languages were listed and eleven were not, so a Hungarian
 * user read "nincs jelentés" where the card should have said "unknown".
 *
 * The integration's KEYWORDS map in const.py is the source of truth: it is what
 * the parser matches against, so the card is checked against it rather than
 * against a second hand-kept list.
 */
import { describe, expect, it, vi } from 'vitest';
// Vite inlines the file as a string, which keeps this in the jsdom
// environment the card element needs.
// @ts-expect-error - no type declaration for a ?raw import of a .py file
import constPySource from '../../custom_components/bergfex/const.py?raw';

import '../src/bergfex-card';
import type { BergfexCard } from '../src/bergfex-card';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

/**
 * Every `"values"` entry in const.py that the integration maps to `unknown`.
 *
 * Those are exactly the no-report phrases; the remaining entries are avalanche
 * levels and snow qualities, which are real readings and must stay visible.
 */
const noReportPhrasesFromIntegration = (): { lang: string; phrase: string }[] => {
  const source = constPySource as string;
  const found: { lang: string; phrase: string }[] = [];

  // "at": { ... "values": { "x": "unknown", }, ... }
  const langBlocks = source.matchAll(/"([a-z]{2})":\s*\{/g);
  for (const match of langBlocks) {
    const lang = match[1];
    const values = source.slice(match.index).match(/"values":\s*\{([^}]*)\}/);
    if (!values) continue;
    for (const entry of values[1].matchAll(/"([^"]+)":\s*"unknown"/g)) {
      found.push({ lang, phrase: entry[1] });
    }
  }
  return found;
};

const isNA = (card: BergfexCard, state: string): boolean =>
  (card as unknown as { _isNA(state: string): boolean })._isNA(state);

describe('no-report states', () => {
  const card = document.createElement('bergfex-card') as BergfexCard;

  it('finds the phrases in the integration to check against', () => {
    const phrases = noReportPhrasesFromIntegration();
    // Sixteen languages map a phrase to unknown; at and en keep their own
    // wording, which is asserted separately below.
    expect(phrases.length).toBeGreaterThanOrEqual(16);
  });

  it.each(noReportPhrasesFromIntegration())('recognises $lang "$phrase"', ({ phrase }) => {
    expect(isNA(card, phrase)).toBe(true);
  });

  it('recognises the two languages that keep bergfex wording verbatim', () => {
    expect(isNA(card, 'keine Meldung')).toBe(true);
    expect(isNA(card, 'no report')).toBe(true);
  });

  it('recognises what Home Assistant itself writes', () => {
    for (const state of ['', 'unknown', 'unavailable', 'none', 'N/A']) {
      expect(isNA(card, state)).toBe(true);
    }
  });

  it('leaves a real reading alone', () => {
    for (const state of ['Powder', 'Pulver', 'mäßig', 'Firn', 'hard']) {
      expect(isNA(card, state)).toBe(false);
    }
  });
});
