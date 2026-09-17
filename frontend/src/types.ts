export interface LovelaceGridOptions {
  columns?: number | 'full';
  min_columns?: number;
  max_columns?: number;
  rows?: number | 'auto';
  min_rows?: number;
  max_rows?: number;
}

export interface HassDevice {
  id: string;
  name: string;
  integration?: string;
  name_by_user?: string;
}

export interface FrontendLocaleData {
  language: string;
  number_format: 'comma_decimal' | 'decimal_comma' | 'space_comma' | 'system' | 'language' | 'none';
  time_format: '12' | '24' | 'system' | 'am_pm';
  // You can expand this with more properties if needed
}

// A basic representation of the Home Assistant object
export interface HomeAssistant {
  states: { [entity_id: string]: HassEntity };
  entities: { [entity_id: string]: HassEntityRegistryDisplayEntry };
  devices: { [deviceId: string]: HassDevice };
  localize: (key: string, ...args: unknown[]) => string;
  language: string;
  locale: FrontendLocaleData;
  callWS: <T>(message: { type: string; [key: string]: unknown }) => Promise<T>;
  themes?: {
    darkMode?: boolean;
    [key: string]: unknown;
  };
  // You can expand this with more properties from the hass object if needed
}

// A basic representation of a Home Assistant entity state object
export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: {
    friendly_name?: string;
    unit_of_measurement?: string;
    [key: string]: unknown;
  };
  last_changed: string;
  last_updated: string;
}

export interface HassEntityRegistryDisplayEntry {
  entity_id: string;
  display_precision?: number;
  device_id?: string;
  domain?: string;
  platform?: string;
}

// A basic representation of a Lovelace card
export interface LovelaceCard extends HTMLElement {
  hass?: HomeAssistant;
  editMode?: boolean;
  setConfig(config: LovelaceCardConfig): void;
  getCardSize?(): number | Promise<number>;
}

// A basic representation of a Lovelace card configuration
export interface LovelaceCardConfig {
  type: string;
  [key: string]: unknown;
}

export interface LovelaceCardEditor extends HTMLElement {
  hass?: HomeAssistant;
  setConfig(config: LovelaceCardConfig): void;
}

export type ResortConfig = string | { device: string; name?: string };

/**
 * Defaults for every optional card setting.
 *
 * Shared by the card and its editor on purpose: they used to keep separate lists
 * that had drifted apart, so the editor showed toggles as off for options the card
 * was rendering.
 */
export const DEFAULT_CONFIG = {
  show_snow: true,
  show_lifts_slopes: true,
  show_trails: true,
  show_conditions: true,
  show_forecast: false,
  show_trend: false,
  show_link: true,
  show_last_updated: true,
  hide_closed_resorts: false,
  conditions_default_open: false,
  forecast_default_open: false,
} as const;

/**
 * Drop everything from a config that only restates a default.
 *
 * The editor used to write its whole working copy back, defaults and all, so
 * adding a card and toggling one switch saved eleven settings the user never
 * touched - and froze today's defaults into that card forever, so a later change
 * to a default could never reach it.
 */
export function withoutDefaults(config: BergfexCardConfig): BergfexCardConfig {
  const stripped = { ...config } as Record<string, unknown>;

  for (const [key, value] of Object.entries(DEFAULT_CONFIG)) {
    if (stripped[key] === value) delete stripped[key];
  }

  // An empty text field is not a setting either. `sort_by` has no entry in
  // DEFAULT_CONFIG because "unsorted" is the absence of the key, not a value.
  for (const key of ['title', 'sort_by']) {
    const value = stripped[key];
    if (value === undefined || value === '' || value === 'none') delete stripped[key];
  }

  return stripped as BergfexCardConfig;
}

export interface BergfexCardConfig extends LovelaceCardConfig {
  hide_closed_resorts?: boolean;
  resorts: ResortConfig[];
  show_conditions?: boolean;
  show_forecast?: boolean;
  show_last_updated?: boolean;
  show_lifts_slopes?: boolean;
  show_link?: boolean;
  show_snow?: boolean;
  show_trails?: boolean;
  show_trend?: boolean;
  sort_by?: string;
  title?: string;
  conditions_default_open?: boolean;
  forecast_default_open?: boolean;
}
