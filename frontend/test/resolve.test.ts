import { describe, expect, it } from 'vitest';
import { problemMessage, resolveEntity, resolveResort } from '../src/resolve';
import { HomeAssistant } from '../src/types';

/**
 * The point of resolving through here is that a failure carries a reason. The
 * card used to drop anything it could not resolve, so a renamed device, a
 * broken integration and a resort that is simply quiet all looked the same from
 * the outside - an empty card.
 */
const hass = (overrides: Partial<HomeAssistant> = {}): HomeAssistant =>
  ({
    language: 'en',
    locale: { language: 'en', number_format: 'comma_decimal', time_format: '24' },
    states: {},
    entities: {},
    devices: {},
    localize: (key: string) => key,
    callWS: async () => ({}),
    ...overrides,
  }) as unknown as HomeAssistant;

const entity = (entity_id: string, state: string) => ({
  entity_id,
  state,
  attributes: {},
  last_changed: '',
  last_updated: '',
});

describe('resolveEntity', () => {
  it('returns the state when the entity is usable', () => {
    const result = resolveEntity(hass({ states: { 'sensor.snow': entity('sensor.snow', '42') } }), 'sensor.snow', {
      domain: 'sensor',
      numeric: true,
    });

    expect(result.ok).toBe(true);
    expect(result.ok && result.value.state).toBe('42');
  });

  it('reports an entity that is not in hass at all', () => {
    const result = resolveEntity(hass(), 'sensor.gone');

    expect(result).toEqual({ ok: false, problem: { reason: 'not_found', subject: 'sensor.gone' } });
  });

  it('reports an entity that has nothing to say', () => {
    const result = resolveEntity(
      hass({ states: { 'sensor.snow': entity('sensor.snow', 'unavailable') } }),
      'sensor.snow',
    );

    expect(result.ok).toBe(false);
    expect(!result.ok && result.problem.reason).toBe('unavailable');
  });

  it('reports an entity from the wrong domain', () => {
    const result = resolveEntity(hass({ states: { 'light.snow': entity('light.snow', 'on') } }), 'light.snow', {
      domain: 'sensor',
    });

    expect(result).toEqual({
      ok: false,
      problem: { reason: 'wrong_domain', subject: 'light.snow', expected: 'sensor', actual: 'light' },
    });
  });

  it('reports a state that is not a number when one is needed', () => {
    const result = resolveEntity(hass({ states: { 'sensor.snow': entity('sensor.snow', 'plenty') } }), 'sensor.snow', {
      numeric: true,
    });

    expect(result).toEqual({
      ok: false,
      problem: { reason: 'not_numeric', subject: 'sensor.snow', state: 'plenty' },
    });
  });

  it('does not throw before hass has arrived', () => {
    expect(() => resolveEntity(undefined, 'sensor.snow')).not.toThrow();
    expect(resolveEntity(undefined, 'sensor.snow').ok).toBe(false);
  });
});

describe('resolveResort', () => {
  const withResort = () =>
    hass({
      devices: { 'device-ischgl': { id: 'device-ischgl', name: 'Ischgl' } },
      entities: { 'sensor.ischgl_status': { entity_id: 'sensor.ischgl_status', device_id: 'device-ischgl' } },
      states: { 'sensor.ischgl_status': entity('sensor.ischgl_status', 'Open') },
    });

  it('returns the device entities', () => {
    const result = resolveResort(withResort(), 'device-ischgl');

    expect(result.ok).toBe(true);
    expect(result.ok && result.value.entities.map((e) => e.entity_id)).toEqual(['sensor.ischgl_status']);
  });

  it('reports a device id that names nothing', () => {
    const result = resolveResort(withResort(), 'device-gone');

    expect(result).toEqual({ ok: false, problem: { reason: 'not_found', subject: 'device-gone' } });
  });

  it('reports a known device that has no entities', () => {
    const quiet = withResort();
    quiet.entities = {};
    quiet.states = {};

    const result = resolveResort(quiet, 'device-ischgl');

    expect(result.ok).toBe(false);
    expect(!result.ok && result.problem.reason).toBe('unavailable');
  });

  it('does not throw before hass has arrived', () => {
    expect(() => resolveResort(undefined, 'device-ischgl')).not.toThrow();
  });
});

describe('problemMessage', () => {
  it('names the subject', () => {
    const message = problemMessage(hass(), { reason: 'not_found', subject: 'device-gone' });

    expect(message).toContain('device-gone');
    expect(message).not.toContain('component.bergfex-card');
  });

  it('fills in the placeholders a reason carries', () => {
    const message = problemMessage(hass(), {
      reason: 'wrong_domain',
      subject: 'light.snow',
      expected: 'sensor',
      actual: 'light',
    });

    expect(message).toContain('sensor');
    expect(message).toContain('light');
  });

  it('has a string for every reason', () => {
    const problems = [
      { reason: 'not_found', subject: 's' },
      { reason: 'unavailable', subject: 's' },
      { reason: 'wrong_domain', subject: 's', expected: 'sensor', actual: 'light' },
      { reason: 'not_numeric', subject: 's', state: 'x' },
    ] as const;

    for (const problem of problems) {
      // localize echoes the key back when it finds nothing, which is how a
      // missing translation shows up.
      expect(problemMessage(hass(), problem)).not.toContain('component.bergfex-card');
    }
  });
});
