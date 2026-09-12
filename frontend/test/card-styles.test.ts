/**
 * Layout rules the card cannot do without at 400px, the width a Lovelace
 * sidebar column actually gets.
 *
 * These assert the *cascaded* value on the card's own elements, not the
 * presence of a declaration. An earlier version of this file matched the first
 * rule whose selector mentioned a class and looked inside it for the text of a
 * declaration. That catches a deletion and nothing else: a later
 * `.resort-status.open { white-space: normal }`, or a
 * `.details .detail-item-value { width: calc(100% - 32px) }`, undoes one of
 * these rules while leaving the declaration it looked at exactly where it was -
 * and the suite stayed green through all four being overridden.
 *
 * So the markup here comes from a real render of the card, the compiled
 * stylesheet is attached to it, and `getComputedStyle` resolves the whole
 * cascade: specificity, source order and shorthands included. The last
 * `describe` proves the harness notices an override rather than only a
 * deletion; without it these assertions would be decoration again the moment
 * the stylesheet stopped reaching the elements.
 *
 * jsdom does no layout, so what this pins is the resolved declared value. The
 * end-to-end suite drives a real browser for anything that needs a box.
 */
import { beforeAll, describe, expect, it, vi } from 'vitest';
import * as sass from 'sass';

import '../src/bergfex-card';
import type { BergfexCard } from '../src/bergfex-card';
import type { BergfexCardConfig, HomeAssistant } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

vi.mock('../src/localize.ts', () => ({
  // Long enough to be the case that broke: "SUMMER SEASON" over two lines.
  localize: (_hass: unknown, key: string) => key.split('.').pop()!.replace(/_/g, ' ').toUpperCase(),
}));

/**
 * Compiled by path, not through a `?raw` import: Vitest replaces the contents
 * of every stylesheet it is asked to import with an empty string unless
 * `css: true`, and it does so silently. A harness fed an empty stylesheet
 * reports the initial value of every property and passes assertions that read
 * `min-width: auto` as "no fixed width" - so the file is read by sass itself.
 */
const SCSS = 'frontend/src/styles/card.styles.scss';

/** `[selectorList, declarations]` for every top-level rule, in source order. */
const rules = (css: string): [string, string][] => {
  const out: [string, string][] = [];
  let depth = 0;
  let selector = '';
  let body = '';

  for (const ch of css) {
    if (ch === '{') {
      depth += 1;
      if (depth === 1) continue;
    } else if (ch === '}') {
      depth -= 1;
      if (depth === 0) {
        out.push([selector.trim(), body]);
        selector = '';
        body = '';
        continue;
      }
    }
    if (depth === 0) selector += ch;
    else body += ch;
  }

  const nested = out.find(([s]) => s.startsWith('@'));
  // At-rules nest, and both the flattening and the no-silent-drop check below
  // only look one level deep. Refusing here is the point: a `@media` block
  // added later must not slip past this file unchecked.
  expect(nested?.[0], 'this harness does not descend into at-rules yet').toBeUndefined();

  return out;
};

/**
 * The stylesheet as it applies to a light-DOM copy of the card's markup.
 *
 * `:host` and `::slotted()` select nothing outside a shadow root, and jsdom
 * drops the *entire* rule when a selector list contains one - which is how
 * `.card-content`'s `overflow-wrap` silently read as `normal` here while being
 * perfectly present in the file and applied in a browser. Dropping only the
 * shadow-only halves of each list keeps the rest of the rule alive.
 */
const lightTree = (css: string): string =>
  rules(css)
    .map(([selector, body]): [string, string] => [
      selector
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s && !s.includes(':host') && !s.includes('::slotted'))
        .join(', '),
      body,
    ])
    .filter(([selector]) => selector)
    .map(([selector, body]) => `${selector} {${body}}`)
    .join('\n');

const DEVICE = 'device-ischgl';

const hass = (): HomeAssistant => {
  const entity = (key: string, state: string, attributes: Record<string, unknown> = {}) =>
    [
      `sensor.ischgl_${key}`,
      {
        entity_id: `sensor.ischgl_${key}`,
        state,
        attributes: { friendly_name: `Ischgl ${key}`, ...attributes },
        last_changed: new Date().toISOString(),
        last_updated: new Date().toISOString(),
      },
    ] as const;

  const states = Object.fromEntries([
    entity('status', 'Open', { link: 'https://example.invalid/' }),
    entity('operation_status', 'täglich'),
    entity('snow_valley', '120', { unit_of_measurement: 'cm' }),
    entity('snow_mountain', '210', { unit_of_measurement: 'cm' }),
    entity('new_snow', '15', { unit_of_measurement: 'cm' }),
    entity('lifts_open_count', '32', { total: '41' }),
    entity('slopes_open_km', '180', { unit_of_measurement: 'km', total: '239' }),
    entity('slopes_open_count', '45', { total: '52' }),
    entity('slope_condition', 'fahrbar'),
    entity('last_update', new Date().toISOString()),
  ]);

  return {
    localize: (key: string) => key,
    language: 'en',
    locale: { language: 'en', number_format: 'comma_decimal', time_format: '24' },
    states,
    entities: Object.fromEntries(Object.keys(states).map((id) => [id, { entity_id: id, device_id: DEVICE }])),
    devices: { [DEVICE]: { id: DEVICE, name: 'Ischgl' } },
    callWS: vi.fn(),
  } as unknown as HomeAssistant;
};

/** The card's own rendered markup, with the compiled stylesheet applied to it. */
const styled = async (extra = ''): Promise<(selector: string) => CSSStyleDeclaration> => {
  const card = document.createElement('bergfex-card') as BergfexCard;
  document.body.appendChild(card);
  card.hass = hass();
  card.setConfig({
    type: 'custom:bergfex-card',
    resorts: [DEVICE],
    show_slopes: true,
    show_lifts: true,
  } as BergfexCardConfig);
  await card.updateComplete;

  const rendered = card.shadowRoot!.innerHTML;
  card.remove();

  const css = `${lightTree(sass.compile(SCSS, { style: 'expanded' }).css)}\n${extra}`;

  document.head.innerHTML = '';
  const sheet = document.createElement('style');
  sheet.textContent = css;
  document.head.appendChild(sheet);
  document.body.innerHTML = rendered;

  // Two ways for this harness to go quietly blind, both of which look exactly
  // like "the rule was never overridden": the engine can drop a rule while
  // parsing, or it can keep the rule and then fail to match its selector. The
  // second is not hypothetical - a selector list containing `::slotted()`
  // parses fine here and matches nothing, which is how `.card-content` once
  // reported `overflow-wrap: normal` from a file that plainly sets it.
  const declared = rules(css).map(([selector]) => selector);
  const parsed = Array.from((sheet.sheet as CSSStyleSheet).cssRules, (rule) => (rule as CSSStyleRule).selectorText);
  const collapse = (s: string) => s.replace(/\s+/g, ' ').trim();
  const missing = declared.filter((s) => !parsed.some((p) => collapse(p) === collapse(s)));
  expect(parsed.length, `the style engine dropped these rules: ${missing.join(' | ')}`).toBe(declared.length);

  return (selector: string) => {
    const element = document.querySelector(selector);
    expect(element, `the card rendered no ${selector}`).not.toBeNull();

    const reached = parsed.some((rule) => {
      try {
        return element!.matches(rule);
      } catch {
        return false;
      }
    });
    expect(reached, `no rule in the stylesheet reaches ${selector}: it is being read unstyled`).toBe(true);

    return getComputedStyle(element!);
  };
};

describe('card.styles.scss at 400px', () => {
  let style: (selector: string) => CSSStyleDeclaration;

  beforeAll(async () => {
    style = await styled();
  });

  it('keeps the status badge on one line', () => {
    // "SUMMER SEASON" wrapped into a two-storey badge and dragged the header
    // out of alignment with the resort name beside it.
    expect(style('.resort-status').whiteSpace).toBe('nowrap');
  });

  it('lets a detail item shrink into its grid column', () => {
    // A hard-coded width: calc(100% - 32px) assumed the icon is exactly 32px
    // and still refused to shrink below its content, so a label such as
    // "Slopes (Total)" escaped from under its progress bar.
    const value = style('.detail-item-value');

    expect(value.minWidth).toBe('0px');
    expect(value.width).toBe('auto');
  });

  it('keeps a detail label inside its column', () => {
    const label = style('.detail-item-label');

    expect(label.overflowWrap).toBe('anywhere');
    expect(label.maxWidth).toBe('100%');
  });

  it('breaks a long unbroken title instead of letting it leave the card', () => {
    // Nothing in the file set a wrapping rule at all, so a resort name without
    // spaces ran off the right edge.
    expect(style('.card-content').overflowWrap).toBe('anywhere');
    expect(style('.resort-name').minWidth).toBe('0px');
  });
});

describe('the harness itself', () => {
  it('reads an overridden rule, not merely a deleted one', async () => {
    // The four rules above, undone by later rules of higher specificity - the
    // exact shape of change the old assertions could not see, and the one a
    // QA pass got past them with. Each expectation names the *overriding*
    // value rather than "not the original": a harness whose stylesheet stopped
    // reaching these elements would satisfy "not the original" for free, and
    // that is precisely the failure being guarded against.
    const overridden = await styled(`
      .resort-status.open { white-space: pre-wrap; }
      .details .detail-item-value { min-width: 120px; width: 300px; }
      .detail-item .detail-item-label { overflow-wrap: break-word; max-width: 42px; }
      .card-content.card-content { overflow-wrap: break-word; }
      .resort-header .resort-name { min-width: 40px; }
    `);

    expect(overridden('.resort-status').whiteSpace).toBe('pre-wrap');
    expect(overridden('.detail-item-value').minWidth).toBe('120px');
    expect(overridden('.detail-item-value').width).toBe('300px');
    expect(overridden('.detail-item-label').overflowWrap).toBe('break-word');
    expect(overridden('.detail-item-label').maxWidth).toBe('42px');
    expect(overridden('.card-content').overflowWrap).toBe('break-word');
    expect(overridden('.resort-name').minWidth).toBe('40px');
  });
});
