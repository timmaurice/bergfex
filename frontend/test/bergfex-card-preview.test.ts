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
    expect(card.header).toBe('Bergfex');
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
});
