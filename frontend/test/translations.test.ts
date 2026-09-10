// @vitest-environment node
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const here = dirname(fileURLToPath(import.meta.url));
const CARD = resolve(here, '../src/translation');
const INTEGRATION = resolve(here, '../../custom_components/bergfex/translations');

const languagesIn = (dir: string) =>
  readdirSync(dir)
    .filter((name) => name.endsWith('.json'))
    .map((name) => name.replace(/\.json$/, ''))
    .sort();

/** Every string key in a translation file, as dotted paths. */
const keysOf = (path: string): string[] => {
  const walk = (node: Record<string, unknown>, prefix = ''): string[] =>
    Object.entries(node).flatMap(([key, value]) =>
      value && typeof value === 'object'
        ? walk(value as Record<string, unknown>, `${prefix}${key}.`)
        : [`${prefix}${key}`],
    );
  return walk(JSON.parse(readFileSync(path, 'utf8'))).sort();
};

describe('the card translations', () => {
  it('cover at least the languages the integration can be configured in', () => {
    // A resort set up on a Spanish, Italian or Dutch bergfex page was read back
    // through an English card, because the card shipped five languages against
    // the integration's seven.
    const card = languagesIn(CARD);

    for (const language of languagesIn(INTEGRATION)) {
      expect({ language, shipped: card.includes(language) }).toEqual({ language, shipped: true });
    }
  });

  it('give every language the same keys as English', () => {
    // localize falls back to English per key, so a gap stays invisible until a
    // user happens to hit that one string.
    const english = keysOf(resolve(CARD, 'en.json'));

    for (const language of languagesIn(CARD)) {
      expect({ language, keys: keysOf(resolve(CARD, `${language}.json`)) }).toEqual({ language, keys: english });
    }
  });
});
