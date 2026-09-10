import { describe, expect, it } from 'vitest';
import { localize } from '../src/localize';
import { HomeAssistant } from '../src/types';

describe('localize', () => {
  it('translates with the language from hass', () => {
    const hass = { language: 'de' } as HomeAssistant;
    expect(localize(hass, 'common.errors.no_resorts')).toBe('Sie müssen mindestens ein Skigebiet definieren.');
  });

  it('falls back to English when hass is not there yet', () => {
    // The card picker renders the preview before it sets hass.
    expect(localize(undefined, 'common.errors.no_resorts')).toBe('You need to define at least one resort entity.');
  });
});
