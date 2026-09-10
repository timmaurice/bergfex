import { HassEntity, HomeAssistant } from './types';
import { localize } from './localize';

/**
 * Why something the config names could not be used.
 *
 * A reason rather than a bare `undefined`, because the card has to be able to
 * tell the user which of these it hit. A resort that was renamed away, one whose
 * integration failed to load, and one that is simply reporting nothing all used
 * to look identical from the outside: an empty card.
 */
export type ResolutionProblem =
  | { reason: 'not_found'; subject: string }
  | { reason: 'unavailable'; subject: string }
  | { reason: 'wrong_domain'; subject: string; expected: string; actual: string }
  | { reason: 'not_numeric'; subject: string; state: string };

export type Resolution<T> = { ok: true; value: T } | { ok: false; problem: ResolutionProblem };

/** States Home Assistant uses to say an entity has nothing to report. */
const UNAVAILABLE_STATES = ['unavailable', 'unknown', 'none', ''];

export interface ResolveEntityOptions {
  /** Require the entity to live in this domain, e.g. 'sensor'. */
  domain?: string;
  /** Require the state to parse as a number. */
  numeric?: boolean;
}

/**
 * Look up one entity and say why it is not usable when it is not.
 */
export function resolveEntity(
  hass: HomeAssistant | undefined,
  entityId: string | undefined,
  options: ResolveEntityOptions = {},
): Resolution<HassEntity> {
  const subject = entityId ?? '';

  if (!hass || !entityId) {
    return { ok: false, problem: { reason: 'not_found', subject } };
  }

  const state = hass.states[entityId];
  if (!state) {
    return { ok: false, problem: { reason: 'not_found', subject } };
  }

  if (options.domain) {
    const actual = entityId.split('.')[0];
    if (actual !== options.domain) {
      return { ok: false, problem: { reason: 'wrong_domain', subject, expected: options.domain, actual } };
    }
  }

  if (UNAVAILABLE_STATES.includes(state.state)) {
    return { ok: false, problem: { reason: 'unavailable', subject } };
  }

  if (options.numeric && Number.isNaN(parseFloat(state.state))) {
    return { ok: false, problem: { reason: 'not_numeric', subject, state: state.state } };
  }

  return { ok: true, value: state };
}

export interface ResolvedResort {
  deviceId: string;
  entities: HassEntity[];
}

/**
 * Look up a resort device and the entities that belong to it.
 *
 * The card is configured with device ids, so this is the resolution that
 * actually decides whether a card row can be drawn. It used to be a silent
 * `return`: a device id that no longer exists - the integration removed, the
 * resort deleted, a config copied between instances - dropped the resort from
 * the list entirely and the user was left looking at an empty card with no
 * indication that anything was wrong.
 */
export function resolveResort(
  hass: HomeAssistant | undefined,
  deviceId: string | undefined,
): Resolution<ResolvedResort> {
  const subject = deviceId ?? '';

  if (!hass || !deviceId || !hass.devices?.[deviceId]) {
    return { ok: false, problem: { reason: 'not_found', subject } };
  }

  const entities = Object.values(hass.states).filter(
    (entity) =>
      hass.entities[entity.entity_id]?.device_id === deviceId &&
      (entity.entity_id.startsWith('sensor.') || entity.entity_id.startsWith('image.')),
  );

  if (entities.length === 0) {
    // The device is known but nothing is reporting for it, which is what a
    // failed config entry looks like from here.
    return { ok: false, problem: { reason: 'unavailable', subject } };
  }

  return { ok: true, value: { deviceId, entities } };
}

/**
 * The localized one-line explanation for a problem.
 *
 * Named after the reason so a new reason cannot be added without a string to go
 * with it.
 */
export function problemMessage(hass: HomeAssistant | undefined, problem: ResolutionProblem): string {
  const placeholders: Record<string, string> = { subject: problem.subject };
  if (problem.reason === 'wrong_domain') {
    placeholders.expected = problem.expected;
    placeholders.actual = problem.actual;
  }
  if (problem.reason === 'not_numeric') {
    placeholders.state = problem.state;
  }

  return localize(hass, `component.bergfex-card.card.warnings.${problem.reason}`, placeholders);
}
