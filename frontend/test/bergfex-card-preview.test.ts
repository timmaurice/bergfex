import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '../src/bergfex-card';
import { BergfexCard } from '../src/bergfex-card';
import { HomeAssistant, BergfexCardConfig } from '../src/types';

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

vi.spyOn(console, 'info').mockImplementation(() => undefined);

// Deliberately NOT mocking ../src/localize: the whole point of the picker
// preview is that the card renders its strings before hass exists, and a stubbed
// localize would pass no matter what the real one does with `hass === undefined`.
// These cases assert the real English text from src/translation/en.json.
const NO_RESORTS_EN = 'You need to define at least one resort entity.';

interface HaCard extends HTMLElement {
  header?: string;
}

describe('BergfexCard card picker preview', () => {
  let element: BergfexCard;
  let hass: HomeAssistant;

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

    element = document.createElement('bergfex-card') as BergfexCard;
    document.body.appendChild(element);
  });

  afterEach(() => {
    document.body.removeChild(element);
  });

  it('accepts the stub config the picker builds, before hass is set', () => {
    const stub = BergfexCard.getStubConfig() as BergfexCardConfig;
    expect(() => element.setConfig(stub)).not.toThrow();
  });

  it('renders the card without hass and without a resort', async () => {
    element.setConfig(BergfexCard.getStubConfig() as BergfexCardConfig);
    await element.updateComplete;

    const card = element.shadowRoot?.querySelector('ha-card') as HaCard;
    expect(card).not.toBeNull();
    // No title: the stub sets only what the user cannot be asked for yet.
    expect(card.header).toBeUndefined();
    expect(card.textContent).toContain(NO_RESORTS_EN);
  });

  it('renders the card once hass arrives but no resort is picked', async () => {
    element.setConfig(BergfexCard.getStubConfig() as BergfexCardConfig);
    element.hass = hass;
    await element.updateComplete;

    const card = element.shadowRoot?.querySelector('ha-card') as HaCard;
    expect(card).not.toBeNull();
    expect(card.textContent).toContain(NO_RESORTS_EN);
  });

  it('still refuses a config without a resorts list, with the real message', () => {
    element.hass = hass;
    expect(() => element.setConfig({ type: 'custom:bergfex-card' } as BergfexCardConfig)).toThrow(NO_RESORTS_EN);
  });

  describe('getStubConfig', () => {
    const withResort = () =>
      ({
        ...hass,
        entities: {
          'sensor.other_thing': { entity_id: 'sensor.other_thing', platform: 'demo', device_id: 'device-demo' },
          'sensor.ischgl_status': {
            entity_id: 'sensor.ischgl_status',
            platform: 'bergfex',
            device_id: 'device-ischgl',
          },
        },
      }) as HomeAssistant;

    it('does not throw when it is called before hass exists', () => {
      expect(() => BergfexCard.getStubConfig()).not.toThrow();
      expect(BergfexCard.getStubConfig()).toEqual({ resorts: [] });
    });

    it('picks the first bergfex resort it is offered', () => {
      const stub = BergfexCard.getStubConfig(withResort(), ['sensor.other_thing', 'sensor.ischgl_status']);

      expect(stub).toEqual({ resorts: ['device-ischgl'] });
    });

    it('falls back to the registry when the picker offers nothing', () => {
      expect(BergfexCard.getStubConfig(withResort(), [])).toEqual({ resorts: ['device-ischgl'] });
    });

    it('offers an empty list when the instance has no resort', () => {
      expect(BergfexCard.getStubConfig(hass, ['sensor.other_thing'])).toEqual({ resorts: [] });
    });

    it('returns nothing that already has a default', () => {
      // Writing a default into the saved config freezes today's value into
      // every card anyone adds, so the stub must set no more than `resorts`.
      const stub = BergfexCard.getStubConfig(withResort());

      expect(Object.keys(stub)).toEqual(['resorts']);
    });
  });

  describe('sizing', () => {
    it('grows with the number of resorts', () => {
      element.setConfig({ type: 'custom:bergfex-card', resorts: ['a'] } as BergfexCardConfig);
      const one = element.getCardSize();
      element.setConfig({ type: 'custom:bergfex-card', resorts: ['a', 'b', 'c'] } as BergfexCardConfig);

      expect(element.getCardSize()).toBeGreaterThan(one);
    });

    it('grows with the sections that are switched on', () => {
      element.setConfig({
        type: 'custom:bergfex-card',
        resorts: ['a'],
        show_snow: false,
        show_lifts_slopes: false,
        show_conditions: false,
        show_trails: false,
      } as BergfexCardConfig);
      const bare = element.getCardSize();

      element.setConfig({
        type: 'custom:bergfex-card',
        resorts: ['a'],
        show_forecast: true,
        forecast_default_open: true,
      } as BergfexCardConfig);

      expect(element.getCardSize()).toBeGreaterThan(bare);
    });

    it('asks a sections dashboard for as many rows as it needs', () => {
      element.setConfig({ type: 'custom:bergfex-card', resorts: ['a', 'b'] } as BergfexCardConfig);
      const options = element.getGridOptions();

      expect(options.rows).toBe(element.getCardSize());
      expect(options.min_rows).toBeLessThanOrEqual(options.rows);
      expect(options.columns).toBeGreaterThan(0);
    });
  });
});
