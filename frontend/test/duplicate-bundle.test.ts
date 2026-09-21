import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
// `?raw` rather than node:fs: these specs run in jsdom, which has no node
// built-ins - the same reason the Playwright specs are excluded in vitest.config.
import bundleSource from '../../custom_components/bergfex/bergfex-card.js?raw';

/**
 * Migration blocker B2, exercised against the artefact that actually ships.
 *
 * A user upgrading from the standalone lovelace-bergfex-card keeps its HACS
 * resource until they uninstall it, so for a while two bundles load into the
 * same page and both reach for the element name `bergfex-card`. The second
 * `customElements.define` throws at module scope, which does not merely lose the
 * second copy - it takes down whichever bundle happens to load second, card and
 * editor alike, and the dashboard renders an error where the card was.
 *
 * The guard exists in the source, but nothing had ever loaded two copies to find
 * out whether it works. These tests evaluate the built bundle twice, which is as
 * close to the browser's view as a test can get: the file under
 * custom_components/ is the one Home Assistant serves.
 *
 * Because it reads the built file, this tests the committed bundle rather than
 * the current source. That is deliberate - a stale bundle shipping to users is
 * itself the failure - but it does mean `npm run build` comes first when the
 * registration code changes.
 */

const ELEMENT = 'bergfex-card';

/**
 * Evaluate the shipped bundle as a browser would on a fresh page load.
 *
 * The one edit is the trailing `export{...}` rollup emits: `new Function` cannot
 * parse a module-level export, and nothing here reads it. Everything that
 * decides the behaviour under test - the `customElements` registration and the
 * `window.customCards` push - runs at module scope and is left untouched.
 */
const loadBundle = (): void => {
  new Function(bundleSource.replace(/export\s*\{[^}]*\}\s*;?\s*$/, ''))();
};

describe('a leftover copy of the standalone card', () => {
  // A custom element cannot be unregistered, so the registry carries across the
  // tests in this file. Rather than fight that, load our bundle once here and
  // let each test add one more copy on top - which is the situation under test
  // anyway, and makes every assertion a delta rather than an absolute.
  beforeAll(() => {
    vi.spyOn(console, 'info').mockImplementation(() => undefined);
    loadBundle();
  });

  beforeEach(() => {
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('registers the element on the first load', () => {
    expect(customElements.get(ELEMENT)).toBeDefined();
  });

  it('does not throw when a second bundle claims the same element', () => {
    const first = customElements.get(ELEMENT);

    // The HACS copy loading after ours - or ours after it; the order is the
    // browser's to decide and neither must be fatal.
    expect(() => loadBundle()).not.toThrow();

    // The first definition stays in charge. A custom element cannot be
    // redefined, so this is the only outcome that leaves a working card.
    expect(customElements.get(ELEMENT)).toBe(first);
  });

  it('says why it stayed inactive', () => {
    const warn = vi.mocked(console.warn);
    loadBundle();

    expect(warn).toHaveBeenCalledTimes(1);
    const message = warn.mock.calls[0]?.join(' ') ?? '';
    // Naming HACS matters: the resource is not something the user can find from
    // a generic "already defined" message.
    expect(message).toContain(ELEMENT);
    expect(message).toContain('HACS');
  });

  it('does not offer the card twice in the picker', () => {
    loadBundle();

    const entries = (window.customCards ?? []).filter((card) => card.type === ELEMENT);
    expect(entries).toHaveLength(1);
  });
});
