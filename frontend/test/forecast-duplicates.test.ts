/**
 * Forecast images left behind by a change of unique id scheme.
 *
 * The integration has keyed its entities three different ways over time, and
 * where an installation carries rows from more than one scheme the registry
 * holds both. The superseded ones have no entity behind them any more - Home
 * Assistant keeps them in `states` as `unavailable` with `restored` set - and
 * they sit on the same device as the live ones. The carousel collected all of
 * them, so Solden offered twelve daily images instead of six and every second
 * slot rendered "Image not available".
 */
import { describe, expect, it, vi } from 'vitest';

import '../src/bergfex-card';
import type { BergfexCard } from '../src/bergfex-card';
import type { BergfexCardConfig, HomeAssistant } from '../src/types';

/** `Resort` is internal to the card; only the two lists matter here. */
type Resort = { forecast_days?: string[]; forecast_summaries?: string[] };

vi.mock('../src/svg/mountain-peak.svg', () => ({ default: '' }));
vi.mock('../src/svg/mountain-valley.svg', () => ({ default: '' }));
vi.mock('../src/svg/classic-cross-country-skiing.svg', () => ({ default: '' }));
vi.mock('../src/svg/skating-cross-country-skiing.svg', () => ({ default: '' }));

const DEVICE = 'device-solden';

type Row = { id: string; restored?: boolean };

const buildHass = (rows: Row[]): HomeAssistant => {
  const states: Record<string, unknown> = {};
  const entities: Record<string, unknown> = {};

  for (const { id, restored } of rows) {
    states[id] = {
      entity_id: id,
      state: restored ? 'unavailable' : 'idle',
      attributes: restored ? { restored: true } : { entity_picture: `/api/image_proxy/${id}` },
      last_changed: '',
      last_updated: '',
    };
    entities[id] = { device_id: DEVICE };
  }

  return {
    language: 'en',
    locale: { language: 'en', number_format: 'comma_decimal', time_format: '24' },
    states,
    entities,
    devices: { [DEVICE]: { id: DEVICE, name: 'Sölden' } },
    localize: (key: string) => key,
  } as unknown as HomeAssistant;
};

const resortFrom = (rows: Row[]): Resort => {
  const element = document.createElement('bergfex-card') as BergfexCard;
  const hass = buildHass(rows);
  const config = { type: 'custom:bergfex-card', resorts: [DEVICE] } as BergfexCardConfig;

  const resorts = (
    element as unknown as {
      _getResorts(h: HomeAssistant, c: BergfexCardConfig): Record<string, Resort>;
    }
  )._getResorts(hass, config);

  return resorts[DEVICE];
};

/** What the registry looks like on an installation that has both schemes. */
const soldenRows = (): Row[] => {
  const rows: Row[] = [{ id: 'sensor.solden_status' }];
  for (let day = 0; day < 6; day++) {
    rows.push({ id: `image.solden_forecast_image_day_${day}` });
    rows.push({ id: `image.solden_forecast_image_day_${day}_2`, restored: true });
  }
  for (const hours of [48, 72, 96, 120, 144]) {
    rows.push({ id: `image.solden_summary_image_${hours}h` });
    rows.push({ id: `image.solden_summary_image_${hours}h_2`, restored: true });
  }
  return rows;
};

describe('forecast images left over from an older unique id scheme', () => {
  it('offers one daily image per day, not two', () => {
    const resort = resortFrom(soldenRows());

    expect(resort.forecast_days).toEqual([
      'image.solden_forecast_image_day_0',
      'image.solden_forecast_image_day_1',
      'image.solden_forecast_image_day_2',
      'image.solden_forecast_image_day_3',
      'image.solden_forecast_image_day_4',
      'image.solden_forecast_image_day_5',
    ]);
  });

  it('offers one summary per interval, not two', () => {
    const resort = resortFrom(soldenRows());

    expect(resort.forecast_summaries).toEqual([
      'image.solden_summary_image_48h',
      'image.solden_summary_image_72h',
      'image.solden_summary_image_96h',
      'image.solden_summary_image_120h',
      'image.solden_summary_image_144h',
    ]);
  });

  it('keeps the day and its image aligned', () => {
    // The label is read out of the entity id, so a dead entity in the list did
    // not merely blank one slot - it shifted every day after it.
    const resort = resortFrom(soldenRows());

    resort.forecast_days?.forEach((id: string, index: number) => {
      expect(id).toContain(`day_${index}`);
    });
  });

  it('leaves a clean installation exactly as it was', () => {
    const clean = soldenRows().filter((row) => !row.restored);

    const resort = resortFrom(clean);

    expect(resort.forecast_days).toHaveLength(6);
    expect(resort.forecast_summaries).toHaveLength(5);
  });

  it('still shows an image whose resort is merely unavailable', () => {
    // Only `restored` marks a row with nothing behind it. A resort whose
    // coordinator is failing is unavailable too, and hiding that would turn an
    // outage into an empty carousel with no explanation.
    const rows: Row[] = [
      { id: 'sensor.solden_status' },
      { id: 'image.solden_forecast_image_day_0' },
      { id: 'image.solden_forecast_image_day_1' },
    ];
    const hass = buildHass(rows);
    hass.states['image.solden_forecast_image_day_1'] = {
      entity_id: 'image.solden_forecast_image_day_1',
      state: 'unavailable',
      attributes: {},
      last_changed: '',
      last_updated: '',
    } as never;

    const element = document.createElement('bergfex-card') as BergfexCard;
    const resorts = (
      element as unknown as {
        _getResorts(h: HomeAssistant, c: BergfexCardConfig): Record<string, Resort>;
      }
    )._getResorts(hass, { type: 'custom:bergfex-card', resorts: [DEVICE] } as BergfexCardConfig);

    expect(resorts[DEVICE].forecast_days).toHaveLength(2);
  });
});
