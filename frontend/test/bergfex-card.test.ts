import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '../src/bergfex-card';
import * as utils from '../src/utils';
import { BergfexCard } from '../src/bergfex-card';
import { HomeAssistant, BergfexCardConfig } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

vi.mock('../src/localize.ts', () => ({
  localize: (_hass: unknown, key: string) => {
    const parts = key.split('.');
    return parts[parts.length - 1]
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  },
}));

// Mock console.info
vi.spyOn(console, 'info').mockImplementation(() => undefined);

// Define a minimal interface for the ha-card element
interface HaCard extends HTMLElement {
  header?: string;
}

/**
 * Creates a mock resort with entities and states.
 * @param id - A unique identifier for the resort (e.g., 'ischgl').
 * @param name - The friendly name of the resort.
 * @param data - An object with resort data.
 * @returns An object containing entities, states, and devices for the mock resort.
 */
const createMockResort = (
  id: string,
  name: string,
  data: {
    status: 'Open' | 'Closed';
    link?: string;
    avalanche_warning?: string;
    classical_condition?: string;
    classical_total_km_attr?: string;
    classical_open_km?: string;
    forecast_days?: boolean;
    forecast_summaries?: boolean;
    last_snowfall?: string;
    last_update?: string;
    season_attrs?: Record<string, string>;
    lifts_open?: string;
    lifts_open_count?: string;
    lifts_total?: string;
    new_snow?: string;
    operation_status?: string;
    skating_condition?: string;
    skating_total_km_attr?: string;
    skating_open_km?: string;
    slope_condition?: string;
    slopes_open?: string; // Fallback
    slopes_open_count?: string; // New
    slopes_open_km?: string;
    slopes_total?: string;
    slopes_total_km?: string;
    snow_condition?: string;
    snow_mountain?: string;
    snow_valley?: string;
  },
) => {
  const device_id = `device-${id}`;
  const states: HomeAssistant['states'] = {};
  const entities: HomeAssistant['entities'] = {};
  const devices: HomeAssistant['devices'] = {};

  devices[device_id] = {
    id: device_id,
    name: name,
  };

  const createEntity = (key: string, state: string, unit?: string, extraAttributes: Record<string, unknown> = {}) => {
    const entity_id = key.startsWith('image.') ? key : `sensor.${id}_${key}`;

    entities[entity_id] = { entity_id, device_id };

    states[entity_id] = {
      entity_id,
      state,
      attributes: { friendly_name: `${name} ${key}`, unit_of_measurement: unit, ...extraAttributes },
      last_changed: new Date().toISOString(),
      last_updated: new Date().toISOString(),
    };
  };

  createEntity('status', data.status, undefined, { link: data.link, ...(data.season_attrs ?? {}) });
  if (data.operation_status) createEntity('operation_status', data.operation_status);
  if (data.snow_valley) createEntity('snow_valley', data.snow_valley, 'cm');
  if (data.snow_mountain) createEntity('snow_mountain', data.snow_mountain, 'cm');
  if (data.new_snow) createEntity('new_snow', data.new_snow, 'cm');
  if (data.lifts_open_count) {
    createEntity('lifts_open_count', data.lifts_open_count, undefined, { total: data.lifts_total });
  } else if (data.lifts_open) {
    createEntity('lifts_open', data.lifts_open, undefined, { total: data.lifts_total });
  }
  if (data.slopes_open_km) createEntity('slopes_open_km', data.slopes_open_km, 'km', { total: data.slopes_total_km });
  if (data.slopes_open_count) {
    createEntity('slopes_open_count', data.slopes_open_count, undefined, { total: data.slopes_total });
  } else if (data.slopes_open) {
    createEntity('slopes_open', data.slopes_open, undefined, { total: data.slopes_total });
  }

  if (data.classical_open_km) {
    createEntity('classical_open_km', data.classical_open_km, 'km', { total: data.classical_total_km_attr });
  }
  if (data.skating_open_km) {
    createEntity('skating_open_km', data.skating_open_km, 'km', { total: data.skating_total_km_attr });
  }
  if (data.classical_condition) createEntity('classical_condition', data.classical_condition);
  if (data.skating_condition) createEntity('skating_condition', data.skating_condition);
  if (data.slope_condition) createEntity('slope_condition', data.slope_condition);
  if (data.snow_condition) createEntity('snow_condition', data.snow_condition);
  if (data.last_snowfall) createEntity('last_snowfall', data.last_snowfall);
  if (data.avalanche_warning) createEntity('avalanche_warning', data.avalanche_warning);
  createEntity('last_update', data.last_update ?? new Date().toISOString());

  if (data.forecast_days) {
    for (let i = 0; i < 6; i++) {
      createEntity(`image.${id}_snow_forecast_day_${i}`, new Date().toISOString(), undefined, {
        entity_picture: `/local/images/day_${i}.png`,
      });
    }
  }

  if (data.forecast_summaries) {
    [48, 72, 96].forEach((h) => {
      createEntity(`image.${id}_snow_forecast_summary_${h}h`, new Date().toISOString(), undefined, {
        entity_picture: `/local/images/summary_${h}h.png`,
      });
    });
  }

  return { entities, states, devices, device_id };
};

describe('BergfexCard', () => {
  let element: BergfexCard;
  let hass: HomeAssistant;
  let config: BergfexCardConfig;
  const fireEventSpy = vi.spyOn(utils, 'fireEvent');

  /**
   * Helper function to set up the card element with a given configuration and mock stations.
   * @param configUpdates - Partial configuration to apply.
   * @param resorts - An array of mock resort objects.
   */
  const setupCard = async (
    configUpdates: Partial<BergfexCardConfig>,
    ...resorts: ReturnType<typeof createMockResort>[]
  ) => {
    Object.assign(config, configUpdates);
    if (!configUpdates.resorts) {
      config.resorts = resorts.map((s) => s.device_id);
    }
    hass.entities = resorts.reduce((acc, s) => ({ ...acc, ...s.entities }), {});
    hass.states = resorts.reduce((acc, s) => ({ ...acc, ...s.states }), {});
    hass.devices = resorts.reduce((acc, s) => ({ ...acc, ...s.devices }), {});
    element.hass = hass;
    element.setConfig(config);
    await element.updateComplete;
  };

  beforeEach(() => {
    hass = {
      localize: (key: string) => key,
      language: 'en',
      locale: {
        language: 'en',
        number_format: 'comma_decimal',
        time_format: '24',
      },
      states: {},
      entities: {},
      devices: {},
      callWS: vi.fn(),
    } as HomeAssistant;

    config = {
      type: 'custom:bergfex-card',
      resorts: [],
    };

    element = document.createElement('bergfex-card') as BergfexCard;
    document.body.appendChild(element);
  });

  afterEach(() => {
    document.body.removeChild(element);
  });

  describe('Initialization and Configuration', () => {
    it('should create the component instance', () => {
      expect(element).toBeInstanceOf(HTMLElement);
      expect(element.tagName.toLowerCase()).toBe('bergfex-card');
    });

    it('should throw an error if no resorts are provided', () => {
      element.hass = hass; // Set hass before calling setConfig
      expect(() => element.setConfig({ type: 'custom:bergfex-card' } as BergfexCardConfig)).toThrow('No Resorts');
    });
  });

  describe('Rendering', () => {
    it('should render a title if provided', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open' });
      await setupCard({ title: 'Ski Resorts' }, resort);

      const card = element.shadowRoot?.querySelector<HaCard>('ha-card');
      expect(card?.header).toBe('Ski Resorts');
    });

    it('should render resort details correctly', async () => {
      const resortData = {
        status: 'Open' as const,
        snow_mountain: '150',
        snow_valley: '30',
        new_snow: '10',
        lifts_open: '40',
        lifts_total: '45',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const resortEl = element.shadowRoot?.querySelector('.resort');
      expect(resortEl).not.toBeNull();

      expect(resortEl?.querySelector('.resort-name')?.textContent).toBe('Ischgl');
      expect(resortEl?.querySelector('.resort-status')?.textContent).toBe('Open');

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      // Normalize whitespace for more reliable matching
      expect(detailItems?.[0].textContent?.replace(/\s+/g, ' ').trim()).toContain('150 cm'); // snow mountain
      expect(detailItems?.[0].textContent?.replace(/\s+/g, ' ').trim()).toContain('Snow Mountain'); // label

      expect(detailItems?.[1].textContent?.replace(/\s+/g, ' ').trim()).toContain('30 cm'); // snow valley
      expect(detailItems?.[1].textContent?.replace(/\s+/g, ' ').trim()).toContain('Snow Valley'); // label

      expect(detailItems?.[2].textContent?.replace(/\s+/g, ' ').trim()).toContain('10 cm'); // new snow

      // Check that lifts are shown (with progress bar)
      const liftItems = Array.from(detailItems || []).filter((item) => item.textContent?.includes('40/45'));
      expect(liftItems.length).toBeGreaterThan(0);
      expect(liftItems.length).toBeGreaterThan(0);
      expect(liftItems[0].querySelector('.progress-bar-container')).not.toBeNull(); // progress bar
    });

    it('should render lifts open count with total and progress bar', async () => {
      const resortData = {
        status: 'Open' as const,
        lifts_open_count: '30',
        lifts_total: '35',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const liftItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('30/35'));
      expect(liftItem).not.toBeNull();
      expect(liftItem?.querySelector('.progress-bar-container')).not.toBeNull();
    });

    it('should render lifts open count without total (no progress bar)', async () => {
      const resortData = {
        status: 'Open' as const,
        lifts_open_count: '30',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const liftItem = Array.from(detailItems || []).find((item) =>
        item.textContent?.replace(/\s+/g, ' ').trim().includes('30 Lifts Open'),
      );
      expect(liftItem).not.toBeNull();
      expect(liftItem?.querySelector('.progress-bar-container')).toBeNull();
    });

    it('should fallback to lifts_open if lifts_open_count is not provided', async () => {
      const resortData = {
        status: 'Open' as const,
        lifts_open: '25',
        lifts_total: '30',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const liftItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('25/30'));
      expect(liftItem).not.toBeNull();
      expect(liftItem?.querySelector('.progress-bar-container')).not.toBeNull();
    });

    it('should prioritize lifts_open_count over lifts_open if both are provided', async () => {
      const resortData = {
        status: 'Open' as const,
        lifts_open_count: '20',
        lifts_total: '25',
        lifts_open: '15', // Should be ignored
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const liftItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('20/25'));
      expect(liftItem).not.toBeNull();
      expect(liftItem?.querySelector('.progress-bar-container')).not.toBeNull();
      expect(element.shadowRoot?.textContent).not.toContain('15'); // Ensure lifts_open is not rendered
    });

    it('should render slopes open count with total and progress bar', async () => {
      const resortData = {
        status: 'Open' as const,
        slopes_open_count: '25',
        slopes_total: '30',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const slopeItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('25/30'));
      expect(slopeItem).not.toBeNull();
      expect(slopeItem?.querySelector('.progress-bar-container')).not.toBeNull();
    });

    it('should render slopes open count without total (no progress bar)', async () => {
      const resortData = {
        status: 'Open' as const,
        slopes_open_count: '25',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const slopeItem = Array.from(detailItems || []).find((item) =>
        item.textContent?.replace(/\s+/g, ' ').trim().includes('25 Slopes Info'),
      );
      expect(slopeItem).not.toBeNull();
      expect(slopeItem?.querySelector('.progress-bar-container')).toBeNull();
    });

    it('should render slopes open km even without total', async () => {
      const resortData = {
        status: 'Open' as const,
        slopes_open_km: '25',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      // Normalize whitespace
      // We need to find the item with slope icon
      const slopeItem = Array.from(detailItems || []).find((item) =>
        item.querySelector('ha-icon[icon="mdi:slope-downhill"]'),
      );
      expect(slopeItem).not.toBeNull();
      expect(slopeItem?.textContent?.replace(/\s+/g, ' ').trim()).toContain('25 km');
      expect(slopeItem?.querySelector('.progress-bar-container')).toBeNull(); // NO progress bar
    });

    it('should fallback to slopes_open if slopes_open_count is not provided', async () => {
      const resortData = {
        status: 'Open' as const,
        slopes_open: '20',
        slopes_total: '25',
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const slopeItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('20/25'));
      expect(slopeItem).not.toBeNull();
      expect(slopeItem?.querySelector('.progress-bar-container')).not.toBeNull();
    });

    it('should prioritize slopes_open_count over slopes_open if both are provided', async () => {
      const resortData = {
        status: 'Open' as const,
        slopes_open_count: '15',
        slopes_total: '20',
        slopes_open: '10', // Should be ignored
      };
      const resort = createMockResort('ischgl', 'Ischgl', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      const slopeItem = Array.from(detailItems || []).find((item) => item.textContent?.includes('15/20'));
      expect(slopeItem).not.toBeNull();
      expect(slopeItem?.querySelector('.progress-bar-container')).not.toBeNull();
      expect(element.shadowRoot?.textContent).not.toContain('10'); // Ensure slopes_open is not rendered
    });
  });

  describe('Display Options', () => {
    it('should hide snow details when show_snow is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open', snow_mountain: '100' });
      await setupCard({ show_snow: false }, resort);

      const snowIcon = element.shadowRoot?.querySelector('ha-icon[icon="mdi:snowflake-thermometer"]');
      expect(snowIcon).toBeNull();
    });

    it('should hide lift details when show_lifts_slopes is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open', lifts_open: '10' });
      await setupCard({ show_lifts_slopes: false }, resort);

      const liftIcon = element.shadowRoot?.querySelector('ha-icon[icon="mdi:gondola"]');
      expect(liftIcon).toBeNull();
    });

    it('should hide last updated when show_last_updated is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open' });
      await setupCard({ show_last_updated: false }, resort);

      const lastUpdatedEl = element.shadowRoot?.querySelector('.last-updated');
      expect(lastUpdatedEl).toBeNull();
    });

    it.each(['unknown', 'unavailable', '', 'not a date'])(
      'should hide last updated when the timestamp is %s rather than showing "Invalid Date"',
      async (state) => {
        const resort = createMockResort('airolo', 'Airolo', { status: 'Closed', last_update: state });
        await setupCard({ show_last_updated: true }, resort);

        expect(element.shadowRoot?.querySelector('.last-updated')).toBeNull();
        expect(element.shadowRoot?.textContent).not.toContain('Invalid Date');
      },
    );

    it('should still show last updated when the timestamp is valid', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        last_update: new Date().toISOString(),
      });
      await setupCard({ show_last_updated: true }, resort);

      expect(element.shadowRoot?.querySelector('.last-updated')).not.toBeNull();
      expect(element.shadowRoot?.textContent).not.toContain('Invalid Date');
    });

    it('should sort resorts without a timestamp last instead of scrambling the order', async () => {
      const newest = createMockResort('newest', 'Newest', {
        status: 'Open',
        last_update: new Date('2026-08-30T10:00:00Z').toISOString(),
      });
      const older = createMockResort('older', 'Older', {
        status: 'Open',
        last_update: new Date('2026-08-29T10:00:00Z').toISOString(),
      });
      const undated = createMockResort('undated', 'Undated', { status: 'Open', last_update: 'unknown' });

      await setupCard({ sort_by: 'update' }, older, undated, newest);

      const names = Array.from(element.shadowRoot?.querySelectorAll('.resort-name') ?? []).map((el) =>
        el.textContent?.trim(),
      );
      expect(names).toEqual(['Newest', 'Older', 'Undated']);
    });

    it('should ignore null and undefined entries in the resorts config', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open' });

      await expect(
        setupCard(
          {
            resorts: [null, resort.device_id, undefined, null] as unknown as BergfexCardConfig['resorts'],
          },
          resort,
        ),
      ).resolves.not.toThrow();

      const names = Array.from(element.shadowRoot?.querySelectorAll('.resort-name') ?? []).map((el) =>
        el.textContent?.trim(),
      );
      expect(names).toEqual(['Ischgl']);
    });

    it('should show link icon by default if link attribute exists', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open', link: 'https://example.com' });
      await setupCard({}, resort);

      const linkIcon = element.shadowRoot?.querySelector<HTMLAnchorElement>('.link-icon');
      expect(linkIcon).not.toBeNull();
      expect(linkIcon?.href).toBe('https://example.com/');
    });

    it('should hide link icon when show_link is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open', link: 'https://example.com' });
      await setupCard({ show_link: false }, resort);

      const linkIcon = element.shadowRoot?.querySelector('.link-icon');
      expect(linkIcon).toBeNull();
    });
  });

  describe('Sorting', () => {
    it('sorts by open lifts when resorts report lifts_open_count', async () => {
      // The sort read `lifts_open`, which is only mapped when `lifts_open_count`
      // is absent - so for every current resort it compared NaN and did nothing.
      const few = createMockResort('few', 'Few', { status: 'Open', lifts_open_count: '2', lifts_total: '10' });
      const many = createMockResort('many', 'Many', { status: 'Open', lifts_open_count: '9', lifts_total: '10' });
      const mid = createMockResort('mid', 'Mid', { status: 'Open', lifts_open_count: '5', lifts_total: '10' });

      await setupCard({ sort_by: 'lift' }, few, many, mid);

      const names = Array.from(element.shadowRoot?.querySelectorAll('.resort-name') ?? []).map((e) =>
        e.textContent?.trim(),
      );
      expect(names).toEqual(['Many', 'Mid', 'Few']);
    });

    it('still sorts by open lifts when only the legacy lifts_open exists', async () => {
      const few = createMockResort('few', 'Few', { status: 'Open', lifts_open: '2' });
      const many = createMockResort('many', 'Many', { status: 'Open', lifts_open: '9' });

      await setupCard({ sort_by: 'lift' }, few, many);

      const names = Array.from(element.shadowRoot?.querySelectorAll('.resort-name') ?? []).map((e) =>
        e.textContent?.trim(),
      );
      expect(names).toEqual(['Many', 'Few']);
    });
  });

  describe('Status badge', () => {
    const period = (season: 'winter' | 'summer', start: string, end: string) => ({
      [`${season}_season_start`]: start,
      [`${season}_season_end`]: end,
    });

    // Fixed offsets around today so the tests do not drift with the calendar.
    const day = (offset: number) => new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10);

    it('shows Open when the resort is operating, whatever the season', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        season_attrs: period('summer', day(-30), day(30)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.resort-status')?.textContent?.trim()).toBe('Open');
      expect(element.shadowRoot?.querySelector('.resort-status.open')).not.toBeNull();
    });

    it('names the winter season when closed inside it', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: period('winter', day(-30), day(30)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.resort-status')?.textContent?.trim()).toBe('Winter Season');
      expect(element.shadowRoot?.querySelector('.resort-status.winter-season')).not.toBeNull();
    });

    it('names the summer season instead of a bare Closed', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: period('summer', day(-30), day(30)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.resort-status')?.textContent?.trim()).toBe('Summer Season');
      expect(element.shadowRoot?.querySelector('.resort-status.summer-season')).not.toBeNull();
    });

    it('falls back to Closed between the two seasons', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: { ...period('winter', day(60), day(180)), ...period('summer', day(-180), day(-60)) },
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.resort-status')?.textContent?.trim()).toBe('Closed');
      expect(element.shadowRoot?.querySelector('.resort-status.closed')).not.toBeNull();
    });

    it('teases the winter start while the summer season runs', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: { ...period('summer', day(-30), day(30)), ...period('winter', day(60), day(180)) },
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.season-teaser')).not.toBeNull();
    });

    it('teases the winter start between the seasons too', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: period('winter', day(60), day(180)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.season-teaser')).not.toBeNull();
    });

    it('quotes last season as an estimate when the new dates are not published', async () => {
      // bergfex still shows the finished season through the summer.
      const resort = createMockResort('warth', 'Warth', {
        status: 'Closed',
        season_attrs: { ...period('winter', day(-270), day(-140)), ...period('summer', day(-30), day(30)) },
      });
      await setupCard({}, resort);

      const teaser = element.shadowRoot?.querySelector('.season-teaser')?.textContent ?? '';
      expect(teaser).toContain('Season Last Year');
    });

    it('marks a future date as definite, not as an estimate', async () => {
      const resort = createMockResort('serfaus', 'Serfaus', {
        status: 'Closed',
        season_attrs: period('winter', day(90), day(210)),
      });
      await setupCard({}, resort);

      const teaser = element.shadowRoot?.querySelector('.season-teaser')?.textContent ?? '';
      expect(teaser).toContain('Season From');
      expect(teaser).not.toContain('Season Last Year');
    });

    it('drops a stale date rather than calling it last year', async () => {
      // Nearly three years old: no longer a useful estimate.
      const resort = createMockResort('stale', 'Stale', {
        status: 'Closed',
        season_attrs: period('winter', day(-1000), day(-900)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.season-teaser')).toBeNull();
    });

    it('drops the teaser once the winter season has started', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: period('winter', day(-30), day(30)),
      });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.season-teaser')).toBeNull();
    });

    it('shows no teaser for a resort without winter dates', async () => {
      const resort = createMockResort('les-saisies', 'Les Saisies', { status: 'Closed' });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.season-teaser')).toBeNull();
    });

    it('falls back to Closed for a resort that publishes no season at all', async () => {
      const resort = createMockResort('les-saisies', 'Les Saisies', { status: 'Closed' });
      await setupCard({}, resort);
      expect(element.shadowRoot?.querySelector('.resort-status')?.textContent?.trim()).toBe('Closed');
    });
  });

  describe('Condition values', () => {
    it.each(['unknown', 'N/A', 'keine Meldung'])(
      'localizes the placeholder %s instead of printing the raw state',
      async (state) => {
        const resort = createMockResort('ischgl', 'Ischgl', {
          status: 'Open',
          snow_condition: state,
          slope_condition: state,
          last_snowfall: state,
          avalanche_warning: state,
        });
        await setupCard({ show_conditions: true, conditions_default_open: true }, resort);

        const text = element.shadowRoot?.textContent ?? '';
        expect(text).toContain('Unknown');
        expect(text).not.toContain('keine Meldung');
        expect(text.match(/\bunknown\b/)).toBeNull();
      },
    );

    it('leaves a real condition report untouched', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        snow_condition: 'Pulver',
      });
      await setupCard({ show_conditions: true, conditions_default_open: true }, resort);

      expect(element.shadowRoot?.textContent).toContain('Pulver');
    });
  });

  describe('Filtering', () => {
    const period = (season: 'winter' | 'summer', start: string, end: string) => ({
      [`${season}_season_start`]: start,
      [`${season}_season_end`]: end,
    });
    const day = (offset: number) => new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10);

    it('keeps resorts in summer operation, which are not closed', async () => {
      // bergfex reports these as "Sommerbetrieb" and they may be running lifts.
      const summer = createMockResort('warth', 'Warth', {
        status: 'Closed',
        season_attrs: period('summer', day(-30), day(30)),
      });
      await setupCard({ hide_closed_resorts: true }, summer);

      expect(element.shadowRoot?.querySelectorAll('.resort').length).toBe(1);
    });

    it('keeps resorts inside the winter season that are shut for the night', async () => {
      const winter = createMockResort('ischgl', 'Ischgl', {
        status: 'Closed',
        season_attrs: period('winter', day(-30), day(30)),
      });
      await setupCard({ hide_closed_resorts: true }, winter);

      expect(element.shadowRoot?.querySelectorAll('.resort').length).toBe(1);
    });

    it('hides a resort that is between the two seasons', async () => {
      const between = createMockResort('between', 'Between', {
        status: 'Closed',
        season_attrs: { ...period('winter', day(60), day(180)), ...period('summer', day(-180), day(-60)) },
      });
      await setupCard({ hide_closed_resorts: true }, between);

      expect(element.shadowRoot?.querySelectorAll('.resort').length).toBe(0);
    });

    it('hides a closed resort that publishes no season at all', async () => {
      const noSeason = createMockResort('les-saisies', 'Les Saisies', { status: 'Closed' });
      await setupCard({ hide_closed_resorts: true }, noSeason);

      expect(element.shadowRoot?.querySelectorAll('.resort').length).toBe(0);
    });

    it('should hide closed resorts when hide_closed_resorts is true', async () => {
      const resort1 = createMockResort('resort1', 'Resort 1', { status: 'Open' });
      const resort2 = createMockResort('resort2', 'Resort 2', { status: 'Closed' });

      await setupCard({ hide_closed_resorts: true }, resort1, resort2);

      const resortEls = element.shadowRoot?.querySelectorAll('.resort');
      expect(resortEls?.length).toBe(1);
      expect(resortEls?.[0].querySelector('.resort-name')?.textContent).toBe('Resort 1');
    });

    it('should show all resorts when hide_closed_resorts is false or undefined', async () => {
      const resort1 = createMockResort('resort1', 'Resort 1', { status: 'Open' });
      const resort2 = createMockResort('resort2', 'Resort 2', { status: 'Closed' });

      await setupCard({}, resort1, resort2);

      const resortEls = element.shadowRoot?.querySelectorAll('.resort');
      expect(resortEls?.length).toBe(2);
    });
  });

  describe('Forecast Slideshow', () => {
    it('should render forecast section when enabled and data exists', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        forecast_days: true,
        forecast_summaries: true,
      });
      await setupCard({ show_forecast: true }, resort);

      // Open the forecast accordion by finding it by text (works with mock localization)
      const accordionHeaders = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const forecastHeader = accordionHeaders.find((h) => h.textContent?.includes('Forecast')) as HTMLElement;
      forecastHeader?.click();
      await element.updateComplete;

      const forecastContainer = element.shadowRoot?.querySelector('.forecast-container');
      expect(forecastContainer).not.toBeNull();

      const tabs = element.shadowRoot?.querySelectorAll('.forecast-tab');
      expect(tabs?.length).toBeGreaterThan(0);

      const carouselLabel = element.shadowRoot?.querySelector('.carousel-label');
      expect(carouselLabel).not.toBeNull();

      const image = element.shadowRoot?.querySelector('.forecast-image');
      expect(image).not.toBeNull();
      expect(image?.getAttribute('src')).toBe('/local/images/day_0.png');
    });

    it('should switch tabs and update image', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        forecast_days: true,
        forecast_summaries: true,
      });
      await setupCard({ show_forecast: true }, resort);

      // Open the forecast accordion by finding it by text (works with mock localization)
      const accordionHeaders2 = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const forecastHeader2 = accordionHeaders2.find((h) => h.textContent?.includes('Forecast')) as HTMLElement;
      forecastHeader2?.click();
      await element.updateComplete;

      const tabs = element.shadowRoot?.querySelectorAll('.forecast-tab');
      const summaryTab = tabs?.[1] as HTMLElement;
      summaryTab.click();
      await element.updateComplete;

      const carouselLabel = element.shadowRoot?.querySelector('.carousel-label');
      expect(carouselLabel).not.toBeNull(); // Just verify label exists
      const image = element.shadowRoot?.querySelector('.forecast-image');
      expect(image?.getAttribute('src')).toBe('/local/images/summary_48h.png');
    });

    it('should navigate carousel', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        forecast_days: true,
      });
      await setupCard({ show_forecast: true }, resort);

      // Open the forecast accordion by finding it by text (works with mock localization)
      const accordionHeaders = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const forecastHeader = accordionHeaders.find((h) => h.textContent?.includes('Forecast')) as HTMLElement;
      forecastHeader?.click();
      await element.updateComplete;

      const nextBtn = element.shadowRoot?.querySelector('.carousel-btn:last-of-type') as HTMLElement;
      nextBtn.click();
      await element.updateComplete;

      const carouselLabel = element.shadowRoot?.querySelector('.carousel-label');
      expect(carouselLabel).not.toBeNull();
      const image = element.shadowRoot?.querySelector('.forecast-image');
      expect(image?.getAttribute('src')).toBe('/local/images/day_1.png');
    });
  });

  describe('Interactions', () => {
    it('should fire hass-more-info event on click', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open' });
      await setupCard({}, resort);

      const resortEl = element.shadowRoot?.querySelector<HTMLElement>('.resort');
      resortEl?.click();

      expect(fireEventSpy).toHaveBeenCalledWith(element, 'hass-more-info', { entityId: 'sensor.ischgl_status' });
    });
  });

  describe('Trend Indicators', () => {
    it('should render trend icons when show_trend is true and history exists', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        snow_mountain: '150',
        snow_valley: '50',
      });

      // Mock history response
      const mockHistory = {
        'sensor.ischgl_snow_mountain': [{ s: '140' }], // Up
        'sensor.ischgl_snow_valley': [{ s: '60' }], // Down
        // Add minimal content for others if needed, or rely on them being optional in render
      };

      // Mocking callWS
      hass.callWS = vi.fn().mockResolvedValue(mockHistory);

      await setupCard({ show_trend: true }, resort);

      // Force history state update (in real usage it's triggered by _fetchHistory)
      // Since _fetchHistory is async and we want to verify the render,
      // we might need to wait or manually set it if the mock doesn't trigger it fast enough.
      // Actually, my implementation calls _fetchHistory in setConfig.

      await element.updateComplete;

      const upIcon = element.shadowRoot?.querySelector('.trend-icon.up');
      const downIcon = element.shadowRoot?.querySelector('.trend-icon.down');

      expect(upIcon).not.toBeNull();
      expect(downIcon).not.toBeNull();
      expect(upIcon?.getAttribute('icon')).toBe('mdi:trending-up');
      expect(downIcon?.getAttribute('icon')).toBe('mdi:trending-down');
    });

    it('should not render trend icons when show_trend is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        snow_mountain: '150',
      });

      // Mocking callWS
      hass.callWS = vi.fn().mockResolvedValue({ 'sensor.ischgl_snow_mountain': [{ s: '140' }] });

      await setupCard({ show_trend: false }, resort);
      await element.updateComplete;

      const trendIcon = element.shadowRoot?.querySelector('.trend-icon');
      expect(trendIcon).toBeNull();
    });
  });

  describe('Cross-Country Resorts', () => {
    it('should render cross-country details correctly', async () => {
      const resortData = {
        status: 'Open' as const,
        classical_open_km: '15',
        skating_open_km: '10',
        classical_condition: 'Good',
        skating_condition: 'Freshly Prepared',
        operation_status: 'Partly open',
      };
      const resort = createMockResort('xc-resort', 'XC Paradise', resortData);
      await setupCard({ show_lifts_slopes: true, show_conditions: true }, resort);

      const resortEl = element.shadowRoot?.querySelector('.resort');
      expect(resortEl).not.toBeNull();

      expect(resortEl?.querySelector('.resort-name')?.textContent).toBe('XC Paradise');
      expect(resortEl?.querySelector('.resort-status')?.textContent).toBe('Open');

      const detailItems = element.shadowRoot!.querySelectorAll('.detail-item');
      expect(detailItems.length).toBe(2); // classical and skating trails

      // Check for trail details instead of snow/lifts
      const classicalTrailItem = Array.from(detailItems).find((item) => item.textContent?.includes('Classical Trails'));
      expect(classicalTrailItem).not.toBeUndefined();
      expect(classicalTrailItem?.textContent?.replace(/\s+/g, ' ').trim()).toContain('15 km');

      const skatingTrailItem = Array.from(detailItems).find((item) => item.textContent?.includes('Skating Trails'));
      expect(skatingTrailItem).not.toBeUndefined();
      expect(skatingTrailItem?.textContent?.replace(/\s+/g, ' ').trim()).toContain('10 km');

      // Check that ski resort details are NOT present
      expect(element.shadowRoot?.textContent).not.toContain('Snow Mountain');
      expect(element.shadowRoot?.textContent).not.toContain('Lifts');

      // Check conditions accordion
      const accordionHeaders = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const conditionsHeader = accordionHeaders.find((h) => h.textContent?.includes('Conditions')) as HTMLElement;
      conditionsHeader?.click();
      await element.updateComplete;

      const accordionContent = conditionsHeader.nextElementSibling;
      expect(accordionContent?.textContent).toContain('Good'); // classical_condition
      expect(accordionContent?.textContent).toContain('Freshly Prepared'); // skating_condition
      expect(accordionContent?.textContent).toContain('Partly open'); // operation_status
      expect(accordionContent?.textContent).not.toContain('Slope Condition');
    });

    it('should render cross-country trails with total and progress bar', async () => {
      const resortData = {
        status: 'Open' as const,
        classical_open_km: '15',
        classical_total_km_attr: '20',
        skating_open_km: '10',
        skating_total_km_attr: '25',
      };
      const resort = createMockResort('xc-resort-totals', 'XC Totals', resortData);
      await setupCard({ show_lifts_slopes: true }, resort);

      const classicalTrailItem = Array.from(element.shadowRoot!.querySelectorAll('.detail-item')).find((item) =>
        item.textContent?.includes('Classical Trails'),
      );
      expect(classicalTrailItem?.textContent?.replace(/\s+/g, ' ').trim()).toContain('15/20 km');
      expect(classicalTrailItem?.querySelector('.progress-bar-container')).not.toBeNull();

      const skatingTrailItem = Array.from(element.shadowRoot!.querySelectorAll('.detail-item')).find((item) =>
        item.textContent?.includes('Skating Trails'),
      );
      expect(skatingTrailItem?.textContent?.replace(/\s+/g, ' ').trim()).toContain('10/25 km');
      expect(skatingTrailItem?.querySelector('.progress-bar-container')).not.toBeNull();
    });

    it('hides trail statistics when show_trails is false', async () => {
      const resort = createMockResort('loipe', 'Loipe', {
        status: 'Open',
        classical_open_km: '12',
        skating_open_km: '8',
      });
      await setupCard({ show_trails: false }, resort);

      const text = element.shadowRoot?.textContent ?? '';
      expect(text).not.toContain('Classical Trails');
      expect(text).not.toContain('Skating Trails');
    });

    it('shows trail statistics by default', async () => {
      const resort = createMockResort('loipe', 'Loipe', {
        status: 'Open',
        classical_open_km: '12',
        skating_open_km: '8',
      });
      await setupCard({}, resort);

      const text = element.shadowRoot?.textContent ?? '';
      expect(text).toContain('Classical Trails');
      expect(text).toContain('Skating Trails');
    });

    it('leaves ski resorts untouched when show_trails is false', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', { status: 'Open', lifts_open_count: '5', lifts_total: '10' });
      await setupCard({ show_trails: false, show_lifts_slopes: true }, resort);

      expect(element.shadowRoot?.textContent).toContain('5');
      expect(element.shadowRoot?.querySelectorAll('.detail-item').length).toBeGreaterThan(0);
    });

    it('should not render snow details for cross-country resorts even if show_snow is true', async () => {
      const resortData = {
        status: 'Open' as const,
        classical_open_km: '15',
        snow_mountain: '50', // This data exists but should not be shown
      };
      const resort = createMockResort('xc-resort', 'XC Paradise', resortData);
      await setupCard({ show_snow: true }, resort);

      const snowDetail = Array.from(element.shadowRoot?.querySelectorAll('.detail-item') || []).find((item) =>
        item.textContent?.includes('Snow Mountain'),
      );
      expect(snowDetail).toBeUndefined();
    });

    it('should sort cross-country resorts by trail length', async () => {
      const resort1 = createMockResort('resort1', 'Resort A', { status: 'Open', classical_open_km: '20' });
      const resort2 = createMockResort('resort2', 'Resort B', { status: 'Open', classical_open_km: '10' });

      await setupCard({ sort_by: 'classical' }, resort1, resort2);

      const resortEls = element.shadowRoot?.querySelectorAll('.resort .resort-name');
      expect(resortEls?.length).toBe(2);
      // Bigger should be first
      expect(resortEls?.[0].textContent).toBe('Resort A'); // 20km
      expect(resortEls?.[1].textContent).toBe('Resort B'); // 10km
    });
  });

  describe('Default Open Accordions', () => {
    it('should have conditions section open by default if conditions_default_open is true', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        snow_condition: 'Powder',
      });
      await setupCard({ show_conditions: true, conditions_default_open: true }, resort);

      const accordionHeaders = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const conditionsHeader = accordionHeaders.find((h) => h.textContent?.includes('Conditions')) as HTMLElement;

      // Check if content is visible without clicking
      const accordionContent = conditionsHeader.nextElementSibling;
      expect(accordionContent).not.toBeNull();
      expect(accordionContent?.textContent).toContain('Powder');
    });

    it('should have forecast section open by default if forecast_default_open is true', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        forecast_days: true,
      });
      await setupCard({ show_forecast: true, forecast_default_open: true }, resort);

      const accordionHeaders = Array.from(element.shadowRoot?.querySelectorAll('.accordion-header') || []);
      const forecastHeader = accordionHeaders.find((h) => h.textContent?.includes('Forecast')) as HTMLElement;
      expect(forecastHeader).not.toBeNull();

      const forecastContainer = element.shadowRoot?.querySelector('.forecast-container');
      expect(forecastContainer).not.toBeNull();
    });

    it('should allow multiple sections to be open at the same time', async () => {
      const resort = createMockResort('ischgl', 'Ischgl', {
        status: 'Open',
        snow_condition: 'Powder',
        forecast_days: true,
      });
      await setupCard(
        {
          show_conditions: true,
          show_forecast: true,
          conditions_default_open: true,
          forecast_default_open: true,
        },
        resort,
      );

      const conditionsContent = Array.from(element.shadowRoot?.querySelectorAll('.accordion-content') || []).find(
        (el) => el.textContent?.includes('Powder'),
      );
      const forecastContainer = element.shadowRoot?.querySelector('.forecast-container');

      expect(conditionsContent).not.toBeUndefined();
      expect(forecastContainer).not.toBeNull();
    });
  });
});
