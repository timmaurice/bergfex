import { HomeAssistant } from './types';

import da from './translation/da.json';
import de from './translation/de.json';
import en from './translation/en.json';
import es from './translation/es.json';
import fr from './translation/fr.json';
import it from './translation/it.json';
import nl from './translation/nl.json';
import pl from './translation/pl.json';

// The set the integration itself can be configured in, so a resort set up on a
// Spanish, Italian or Dutch bergfex page is not read back through an English
// card. `da` is the card's own extra.
const translations = {
  da,
  de,
  en,
  es,
  fr,
  it,
  nl,
  pl,
};

interface TranslationObject {
  [key: string]: string | TranslationObject;
}

const typedTranslations: { [key: string]: TranslationObject } = translations;

function _getTranslation(language: string, keys: string[]): string | undefined {
  let translation: string | TranslationObject | undefined = typedTranslations[language];
  for (const key of keys) {
    if (typeof translation !== 'object' || translation === null) {
      return undefined;
    }
    translation = translation[key];
  }
  return typeof translation === 'string' ? translation : undefined;
}

export function localize(
  hass: HomeAssistant | undefined,
  key: string,
  placeholders: Record<string, string | number> = {},
): string {
  // The card picker renders a preview before it hands the element its hass, so
  // every localized string has to survive that first pass.
  const lang = hass?.language || 'en';
  const translationKey = key.replace('component.bergfex-card.', '');
  const keyParts = translationKey.split('.');

  const translation = _getTranslation(lang, keyParts) ?? _getTranslation('en', keyParts);

  if (typeof translation === 'string') {
    let finalString = translation;
    for (const placeholder in placeholders) {
      finalString = finalString.replace(`{${placeholder}}`, String(placeholders[placeholder]));
    }
    return finalString;
  }

  return key;
}
