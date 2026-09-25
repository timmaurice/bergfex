/**
 * What the card exposes to assistive technology.
 *
 * Until this suite the card set not one ARIA attribute: every figure was a
 * clickable div a keyboard could not reach, the resort was a focusable div that
 * Enter did nothing on, the carousel arrows had no name, and the link's tooltip
 * printed a translation key. These tests run through the real English strings -
 * not the key-echoing mock the other suites use - because what is under test
 * here is exactly what a screen reader would say.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

// Imported rather than read through node:fs, which the jsdom environment does
// not offer under NODE_ENV=production. translations.test.ts already holds every
// file in the directory to English's keys, so this list cannot fall behind it.
import da from '../src/translation/da.json';
import de from '../src/translation/de.json';
import en from '../src/translation/en.json';
import es from '../src/translation/es.json';
import fr from '../src/translation/fr.json';
import it_ from '../src/translation/it.json';
import nl from '../src/translation/nl.json';
import pl from '../src/translation/pl.json';

import '../src/bergfex-card';
import * as utils from '../src/utils';
import type { BergfexCard } from '../src/bergfex-card';
import type { BergfexCardConfig, HomeAssistant } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

const DEVICE = 'device-ischgl';

type Attributes = Record<string, unknown>;

const hass = (
  sensors: Record<string, [string, Attributes?]>,
  history: Record<string, string> = {},
  images = false,
): HomeAssistant => {
  const states: HomeAssistant['states'] = {};
  const add = (entity_id: string, state: string, attributes: Attributes = {}) => {
    states[entity_id] = {
      entity_id,
      state,
      attributes: { friendly_name: entity_id, ...attributes },
      last_changed: new Date().toISOString(),
      last_updated: new Date().toISOString(),
    };
  };

  for (const [key, [state, attributes]] of Object.entries(sensors)) add(`sensor.ischgl_${key}`, state, attributes);
  if (images) {
    for (let day = 0; day < 3; day++) {
      add(`image.ischgl_forecast_image_day_${day}`, 'ok', { entity_picture: `/day_${day}.png` });
    }
    add('image.ischgl_summary_image_48h', 'ok', { entity_picture: '/summary_48h.png' });
  }

  return {
    localize: (key: string) => key,
    language: 'en',
    locale: { language: 'en', number_format: 'comma_decimal', time_format: '24' },
    states,
    entities: Object.fromEntries(Object.keys(states).map((id) => [id, { entity_id: id, device_id: DEVICE }])),
    devices: { [DEVICE]: { id: DEVICE, name: 'Ischgl' } },
    callWS: vi.fn().mockResolvedValue(Object.fromEntries(Object.entries(history).map(([id, s]) => [id, [{ s }]]))),
  } as unknown as HomeAssistant;
};

const SKI: Record<string, [string, Attributes?]> = {
  status: ['Open', { link: 'https://www.bergfex.at/ischgl/' }],
  snow_mountain: ['210', { unit_of_measurement: 'cm', elevation: 2872 }],
  snow_valley: ['120', { unit_of_measurement: 'cm' }],
  lifts_open_count: ['32', { total: '41' }],
  slopes_open_km: ['180', { unit_of_measurement: 'km', total: '239' }],
  slopes_open_count: ['45'],
  snow_condition: ['Powder'],
  last_update: [new Date(Date.now() - 5 * 60_000).toISOString()],
};

let card: BergfexCard;

const render = async (h: HomeAssistant, config: Partial<BergfexCardConfig> = {}) => {
  card = document.createElement('bergfex-card') as BergfexCard;
  document.body.appendChild(card);
  card.hass = h;
  card.setConfig({ type: 'custom:bergfex-card', resorts: [DEVICE], ...config } as BergfexCardConfig);
  await card.updateComplete;
  // The trend baseline arrives through a promise; let it land and re-render.
  await new Promise((r) => setTimeout(r, 0));
  await card.updateComplete;
  return card.shadowRoot!;
};

/** The figure whose label reads `label`, found the way a screen reader would. */
const item = (root: ShadowRoot, label: string) =>
  Array.from(root.querySelectorAll<HTMLButtonElement>('button.detail-item')).find((b) =>
    b.getAttribute('aria-label')?.startsWith(`${label}:`),
  );

afterEach(() => card?.remove());

describe('the card structure', () => {
  it('names each resort by a heading instead of making a div focusable', async () => {
    const root = await render(hass(SKI));

    expect(root.querySelector('ha-card')?.hasAttribute('tabindex')).toBe(false);

    const resort = root.querySelector('article.resort')!;
    expect(resort.hasAttribute('tabindex')).toBe(false);

    const heading = root.querySelector('h2.resort-name')!;
    expect(heading.textContent).toBe('Ischgl');
    expect(resort.getAttribute('aria-labelledby')).toBe(heading.id);
  });

  it('lets the keyboard open the status through the resort name', async () => {
    const fire = vi.spyOn(utils, 'fireEvent');
    const root = await render(hass(SKI));

    const button = root.querySelector<HTMLButtonElement>('h2.resort-name > button')!;
    expect(button.type).toBe('button');
    button.click();

    // Once, through the resort's own handler.
    const calls = fire.mock.calls.filter(([, type]) => type === 'hass-more-info');
    expect(calls).toEqual([[card, 'hass-more-info', { entityId: 'sensor.ischgl_status' }]]);
    fire.mockRestore();
  });

  it('says "Status" before the badge, without touching the badge text', async () => {
    const root = await render(hass(SKI));

    const group = root.querySelector('.resort-status-group')!;
    expect(group.querySelector('.visually-hidden')?.textContent).toBe('Status:');
    expect(group.querySelector('.resort-status')?.textContent).toBe('Open');
  });

  it('lists the figures, one button per figure', async () => {
    const root = await render(hass(SKI));

    const list = root.querySelector('ul.details')!;
    expect(list.getAttribute('role')).toBe('list');

    const buttons = Array.from(list.querySelectorAll('button.detail-item'));
    expect(buttons.length).toBeGreaterThan(0);
    for (const button of buttons) {
      expect(button.parentElement?.tagName).toBe('LI');
      expect(button.getAttribute('type')).toBe('button');
    }
  });

  it('hides every icon from screen readers', async () => {
    // Each one sits next to text that says the same, or inside a control named
    // in words; read out, they are noise.
    const root = await render(hass(SKI, {}, true), {
      conditions_default_open: true,
      show_forecast: true,
      forecast_default_open: true,
    });

    const icons = Array.from(root.querySelectorAll('ha-icon'));
    expect(icons.length).toBeGreaterThan(5);
    for (const icon of icons) {
      expect({ icon: icon.getAttribute('icon'), hidden: icon.closest('[aria-hidden="true"]') !== null }).toEqual({
        icon: icon.getAttribute('icon'),
        hidden: true,
      });
    }
    for (const svg of Array.from(root.querySelectorAll('.custom-icon'))) {
      expect(svg.getAttribute('aria-hidden')).toBe('true');
    }
  });
});

describe('the figures', () => {
  it('read label first, then value and unit', async () => {
    const root = await render(hass(SKI));

    // Drawn, the value sits above its label and "Mountain" leans on the icon.
    expect(item(root, 'Snow depth on the mountain (2872 m)')?.getAttribute('aria-label')).toBe(
      'Snow depth on the mountain (2872 m): 210 cm',
    );
    expect(item(root, 'Snow depth in the valley')?.getAttribute('aria-label')).toBe('Snow depth in the valley: 120 cm');
  });

  it('read an open/total pair as words', async () => {
    const root = await render(hass(SKI));

    expect(item(root, 'Lifts')?.getAttribute('aria-label')).toBe('Lifts: 32 of 41');
    expect(item(root, 'Slopes (km)')?.getAttribute('aria-label')).toBe('Slopes (km): 180 of 239 km');
    expect(item(root, 'Slopes')?.getAttribute('aria-label')).toBe('Slopes: 45');
  });

  it('say the trend the arrow only shows in colour', async () => {
    const root = await render(hass(SKI, { 'sensor.ischgl_snow_mountain': '200', 'sensor.ischgl_snow_valley': '130' }), {
      show_trend: true,
    });

    expect(item(root, 'Snow depth on the mountain (2872 m)')?.getAttribute('aria-label')).toBe(
      'Snow depth on the mountain (2872 m): 210 cm, up over the last 24 hours',
    );
    expect(item(root, 'Snow depth in the valley')?.getAttribute('aria-label')).toBe(
      'Snow depth in the valley: 120 cm, down over the last 24 hours',
    );
    expect(root.querySelector('.trend-icon.up')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('say "not available" for a missing sensor, and mark it as doing nothing', async () => {
    // SKI carries no new-snow sensor, and the snow row always draws all three.
    const root = await render(hass(SKI));

    const newSnow = item(root, 'New snow')!;
    expect(newSnow.getAttribute('aria-label')).toBe('New snow: not available');
    expect(newSnow.getAttribute('aria-disabled')).toBe('true');
    expect(item(root, 'Lifts')?.hasAttribute('aria-disabled')).toBe(false);
  });

  it('open the entity they show', async () => {
    const fire = vi.spyOn(utils, 'fireEvent');
    const root = await render(hass(SKI));

    item(root, 'Lifts')!.click();

    const calls = fire.mock.calls.filter(([, type]) => type === 'hass-more-info');
    expect(calls).toEqual([[card, 'hass-more-info', { entityId: 'sensor.ischgl_lifts_open_count' }]]);
    fire.mockRestore();
  });

  it('still lay out a cross-country resort recognised by its icon alone', async () => {
    // The card spots a cross-country area partly through the status icon; the
    // markup rework must not lose that.
    const root = await render(
      hass({
        status: ['Open', { icon: 'mdi:ski-cross-country' }],
        classical_open_km: ['12', { unit_of_measurement: 'km', total: '40' }],
      }),
    );

    expect(root.querySelector('ul.details.cross-country-details')).not.toBeNull();
    expect(item(root, 'Classical Trails')?.getAttribute('aria-label')).toBe('Classical Trails: 12 of 40 km');
  });
});

describe('the sections', () => {
  it('are headed, and their toggles say whether they are open', async () => {
    const root = await render(hass(SKI));

    const toggle = root.querySelector<HTMLButtonElement>('h3.accordion-title > button.accordion-header')!;
    expect(toggle.textContent?.trim()).toBe('Conditions');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');

    toggle.click();
    await card.updateComplete;

    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    const content = root.getElementById(toggle.getAttribute('aria-controls')!)!;
    expect(content.textContent).toContain('Powder');
    expect(item(root, 'Snow Condition')?.getAttribute('aria-label')).toBe('Snow Condition: Powder');
  });
});

describe('the forecast', () => {
  const open = async () => render(hass(SKI, {}, true), { show_forecast: true, forecast_default_open: true });

  it('is a tab list with one tab in the tab order', async () => {
    const root = await open();

    const list = root.querySelector('.forecast-tabs')!;
    expect(list.getAttribute('role')).toBe('tablist');
    expect(list.getAttribute('aria-label')).toBe('Snow Forecast');

    const [daily, summary] = Array.from(list.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
    expect([daily.getAttribute('aria-selected'), summary.getAttribute('aria-selected')]).toEqual(['true', 'false']);
    expect([daily.tabIndex, summary.tabIndex]).toEqual([0, -1]);

    const panel = root.getElementById(daily.getAttribute('aria-controls')!)!;
    expect(panel.getAttribute('role')).toBe('tabpanel');
    expect(panel.getAttribute('aria-labelledby')).toBe(daily.id);
  });

  it('moves between the tabs with the arrow keys', async () => {
    const root = await open();
    const daily = root.querySelector<HTMLButtonElement>('[role="tab"]')!;

    daily.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    await card.updateComplete;
    await card.updateComplete;

    const summary = root.querySelectorAll<HTMLButtonElement>('[role="tab"]')[1];
    expect(summary.getAttribute('aria-selected')).toBe('true');
    expect(summary.tabIndex).toBe(0);
    expect(root.activeElement).toBe(summary);
    expect(root.querySelector('.forecast-image')?.getAttribute('src')).toBe('/summary_48h.png');
  });

  it('names the carousel arrows and describes the map', async () => {
    const root = await open();

    const [prev, next] = Array.from(root.querySelectorAll('.carousel-btn'));
    expect(prev.getAttribute('aria-label')).toBe('Previous forecast map');
    expect(next.getAttribute('aria-label')).toBe('Next forecast map');

    expect(root.querySelector('.forecast-image')?.getAttribute('alt')).toBe('Snow forecast map, Today');
    expect(root.querySelector('.forecast-image')?.closest('button')).not.toBeNull();
    expect(root.querySelector('.carousel-label')?.getAttribute('aria-live')).toBe('polite');
  });
});

describe('the footer', () => {
  it('names the bergfex link, and opens it without handing over the card', async () => {
    const root = await render(hass(SKI));

    const link = root.querySelector('a.link-icon')!;
    // The title read a key that does not exist, so the tooltip printed
    // "component.bergfex-card.card.link_title".
    expect(link.getAttribute('aria-label')).toBe('Open Ischgl detail page on bergfex');
    expect(link.getAttribute('title')).toBe('Open Ischgl detail page on bergfex');
    expect(link.getAttribute('rel')).toContain('noopener');
  });

  it('says what the relative time is', async () => {
    const root = await render(hass(SKI));

    const updated = root.querySelector<HTMLButtonElement>('button.last-updated')!;
    expect(updated.getAttribute('aria-label')).toBe('Last updated 5 minutes ago');
    expect(updated.querySelector('time')?.getAttribute('datetime')).toBe(SKI.last_update[0]);
  });
});

describe('the spoken strings', () => {
  const languages: Record<string, { card: Record<'a11y' | 'forecast', Record<string, string>> }> = {
    da,
    de,
    en,
    es,
    fr,
    it: it_,
    nl,
    pl,
  };

  it.each([
    ['a11y', 'value', ['{label}', '{value}']],
    ['a11y', 'of_total', ['{open}', '{total}']],
    ['a11y', 'last_updated', ['{time}']],
    ['forecast', 'image_alt', ['{label}']],
  ] as const)('keep the placeholders of card.%s.%s in every language', (section, key, placeholders) => {
    // localize fills a placeholder only where the translation carries it; a
    // dropped one reads out as a label with no value.
    for (const [language, strings] of Object.entries(languages)) {
      const text = strings.card[section][key];
      for (const placeholder of placeholders) {
        expect({ language, text, has: text.includes(placeholder) }).toEqual({ language, text, has: true });
      }
    }
  });
});
