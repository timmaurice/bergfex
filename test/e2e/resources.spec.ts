import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test, expect } from './fixtures/hass';
import { E2E_DIR, resources, useDashboard } from './helpers/homeassistant';

const CARD_PREFIX = '/bergfex_frontend/';
const CARD_FILENAME = 'bergfex-card.js';

/** The version the integration stamps onto the resource URL. */
const VERSION = (
  JSON.parse(readFileSync(resolve(E2E_DIR, '../../custom_components/bergfex/manifest.json'), 'utf8')) as {
    version: string;
  }
).version;

test.describe('Lovelace resource registration', () => {
  test('has exactly one resource for the bundled card, at the current version', async () => {
    // The registration used to append a resource on every restart. A unit test
    // works against a fake collection; this reads the store Home Assistant
    // actually persisted, after a real start-up.
    const all = await resources();
    const ours = all.filter((resource) => resource.url.startsWith(CARD_PREFIX));

    expect(ours).toHaveLength(1);
    expect(ours[0].url).toBe(`${CARD_PREFIX}${CARD_FILENAME}?v=${VERSION}`);
  });

  test('leaves no resource pointing at a standalone copy of the card', async () => {
    // The card used to be installed separately through HACS. A leftover
    // resource loads a second copy of the bundle, and the second define()
    // throws - which is exactly what the console assertion below catches.
    const strays = (await resources()).filter(
      (resource) => !resource.url.startsWith(CARD_PREFIX) && resource.url.split('?')[0].endsWith(`/${CARD_FILENAME}`),
    );

    expect(strays.map((resource) => resource.url)).toEqual([]);
  });

  test('serves the bundle and defines card and editor without a clash', async ({ page, consoleErrors }) => {
    const urlPath = await useDashboard('resources', { views: [{ title: 'Empty', cards: [] }] });

    await page.goto(`/${urlPath}/0`);
    await page.waitForFunction(() => customElements.get('bergfex-card') !== undefined, {
      timeout: 60_000,
    });

    // The editor is a lazy import: asking the card for its config element is
    // what a user opening the editor does, and it is where a duplicate define()
    // would blow up.
    await page.evaluate(async () => {
      const constructor = customElements.get('bergfex-card') as unknown as {
        getConfigElement(): Promise<HTMLElement>;
      };
      await constructor.getConfigElement();
    });
    await expect.poll(() => page.evaluate(() => !!customElements.get('bergfex-card-editor'))).toBe(true);

    // Registering the card twice used to throw on the second define().
    expect(consoleErrors.filter((text) => /has already been used/i.test(text))).toEqual([]);
  });
});
