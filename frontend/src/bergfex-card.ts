import { LitElement, TemplateResult, html, css, nothing, unsafeCSS } from 'lit';
import { property, state, query } from 'lit/decorators.js';
import {
  HassEntity,
  HomeAssistant,
  LovelaceCard,
  LovelaceCardEditor,
  ResortConfig,
  BergfexCardConfig,
  DEFAULT_CONFIG,
  LovelaceGridOptions,
} from './types.js';
import { classMap } from 'lit/directives/class-map.js';
import { unsafeSVG } from 'lit/directives/unsafe-svg.js';
import { localize } from './localize.js';
import { fireEvent, formatNumber, formatRelativeTime, parseDate, fetchHistory } from './utils.js';
import { ResolutionProblem, problemMessage, resolveResort } from './resolve.js';
import styles from './styles/card.styles.scss';

import mountainIcon from './svg/mountain-peak.svg';
import valleyIcon from './svg/mountain-valley.svg';
import classicCrossCountryIcon from './svg/classic-cross-country-skiing.svg';
import skatingCrossCountryIcon from './svg/skating-cross-country-skiing.svg';

export interface LovelaceHelpers {
  createCardElement(config: { type: string; [key: string]: unknown }): LovelaceCard;
}

interface Resort {
  name?: string;
  /** Set when the resort could not be resolved; the card renders a warning row. */
  problem?: ResolutionProblem;
  status?: string;
  avalanche_warning?: string;
  classical_condition?: string;
  classical_trails_open?: string;
  forecast_days?: string[];
  forecast_summaries?: string[];
  last_snowfall?: string;
  last_update?: string;
  lifts_open?: string;
  lifts_open_count?: string;
  new_snow?: string;
  operation_status?: string;
  skating_condition?: string;
  skating_trails_open?: string;
  slope_condition?: string;
  slopes_open?: string;
  slopes_open_count?: string;
  slopes_open_km?: string;
  snow_condition?: string;
  snow_mountain?: string;
  snow_valley?: string;
  is_cross_country?: boolean;
}

/**
 * Every spelling of "there is no report" this card can be handed.
 *
 * Home Assistant's own unknown/unavailable/none, plus what bergfex prints in
 * each language the integration can be configured in. Compared lower-cased.
 */
const NO_REPORT_STATES = [
  '',
  'n/a',
  'unknown',
  'unavailable',
  'none',
  // Taken from the integration's KEYWORDS map in const.py. Entries marked (live)
  // were read off bergfex directly; the older spellings are kept because bergfex
  // is not consistent between its own pages. The integration normalises what it
  // recognises, so this only has to catch what arrives unnormalised.
  'keine meldung', // at/de
  'no information', // en (live)
  'no info', // en (live)
  'pas de nouvelle', // fr (live)
  'nessuna comunicazione', // it (live)
  'nessun messaggio', // it (live)
  'senza info', // it (live)
  'no hay información', // es (live)
  'ningún mensaje', // es (live)
  'inget meddelande', // se (live)
  'ingen besked', // dk (live)
  'ei ilmoitusta', // fi (live)
  'nincs üzenet', // hu (live)
  'žádné hlášení', // cz (live)
  'žiadne hlásenie', // sk (live)
  'nema poruke', // hr (live)
  'brez sporočila', // si (live)
  'ni obvestila', // si (live)
  'нет сообщений', // ru (live)
  'нет сообщения', // ru (live)
  'fără comunicare', // ro (live)
  'niciun anunţ', // ro (live)
  'no report', // en
  'geen melding', // nl
  'pas de signalement', // fr
  "pas d'info", // fr
  'aucune information', // fr
  'nessuna segnalazione', // it
  'sin información', // es
  'brak komunikatu', // pl
  'nincs jelentés', // hu
  'žádná zpráva', // cz
  'žiadna správa', // sk
  'nema izvješća', // hr
  'ni poročila', // si
  'нет данных', // ru
  'fără raport', // ro
  'ingen rapport', // se
  'ingen melding', // no/dk
  'ei raporttia', // fi
  // Spellings this card carried before the map above was consulted. Kept
  // because bergfex is not always consistent between its own pages.
  'pas de rapport', // fr
  'sin informe', // es
  'brak informacji', // pl
];

type LovelaceCardConstructor = new () => LovelaceCard;
type ForecastTab = 'daily' | 'summary';
type Trend = 'up' | 'down' | 'same';

/** One figure in a resort's grid: what it shows, and what a screen reader says for it. */
interface DetailItem {
  /** Opened in the more-info dialog on activation. Absent when the sensor is. */
  entity?: HassEntity;
  /** Greys the item out: there is no value behind it. */
  na: boolean;
  icon: TemplateResult;
  /** The value as drawn: number, unit, trend arrow and progress bar. */
  value: TemplateResult;
  /** The value as read out, e.g. "32 of 41". */
  valueText: string;
  /** The label as drawn under the value. */
  label: TemplateResult | string;
  /** The label as read out, where the drawn one leans on its icon for context. */
  name: string;
  onClick?: (e: Event) => void;
}

const ELEMENT_NAME = 'bergfex-card';
const EDITOR_ELEMENT_NAME = `${ELEMENT_NAME}-editor`;

declare global {
  interface Window {
    customCards?: {
      type: string;
      name: string;
      description: string;
      documentationURL: string;
      preview?: boolean;
      getEntitySuggestion?: (hass: HomeAssistant, entityId: string) => { config: Record<string, unknown> } | null;
    }[];
    loadCardHelpers(): Promise<LovelaceHelpers>;
  }
}

export class BergfexCard extends LitElement implements LovelaceCard {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @query('ha-card') private _card!: LovelaceCard;
  @state() private _config!: BergfexCardConfig;
  @state() private _forecastState: Record<string, { tab: ForecastTab; index: number }> = {};
  @state() private _accordionState: Record<string, Record<string, boolean>> = {};
  @state() private _historyState: Record<string, string> = {}; // entity_id -> state 24h ago
  // What the baseline in _historyState was fetched for. See _refreshTrendBaseline.
  private _trendBaselineKey?: string;

  public setConfig(config: BergfexCardConfig): void {
    // An empty list is allowed: the card picker configures the card from
    // getStubConfig() to build its preview, long before a resort is picked.
    // Throwing there would leave the picker with a broken tile.
    if (!config || !config.resorts || !Array.isArray(config.resorts)) {
      throw new Error(localize(this.hass, 'common.errors.no_resorts'));
    }
    this._config = {
      ...DEFAULT_CONFIG,
      ...config,
    };

    // No history fetch here. Home Assistant creates the element, calls this,
    // and assigns `hass` afterwards, so at this point there is nothing to fetch
    // with - which is why the trend arrows never appeared on a freshly loaded
    // dashboard. shouldUpdate owns the fetch now, and sees every hass there is.
  }

  public static async getConfigElement(): Promise<LovelaceCardEditor> {
    // Ensure that the required Home Assistant components are loaded before creating the editor
    // by loading a core editor that uses them.
    const helpers = await window.loadCardHelpers();
    const entitiesCard = await helpers.createCardElement({ type: 'entities', entities: [] });
    const constructor = entitiesCard?.constructor as LovelaceCardConstructor & {
      getConfigElement?: () => Promise<LovelaceCardEditor>;
    };
    if (constructor?.getConfigElement) {
      await constructor.getConfigElement();
    }

    await import('./editor.js');
    return document.createElement(EDITOR_ELEMENT_NAME) as LovelaceCardEditor;
  }

  /**
   * The config the card picker previews, and the one "add card" starts from.
   *
   * Called before the element has a hass, on an instance that may have no
   * bergfex resort, so nothing here may throw. Returns `resorts` and nothing
   * else on purpose: writing the other defaults into the saved config would
   * freeze today's defaults into every card anyone adds.
   */
  public static getStubConfig(hass?: HomeAssistant, entities?: string[]): Record<string, unknown> {
    const firstResort = BergfexCard._firstResortDevice(hass, entities);
    return { resorts: firstResort ? [firstResort] : [] };
  }

  /** The device of the first bergfex entity on offer, if there is one. */
  private static _firstResortDevice(hass?: HomeAssistant, entities?: string[]): string | undefined {
    if (!hass?.entities) return undefined;

    // The picker hands over the entities it thinks are relevant; fall back to
    // the whole registry so the stub still finds a resort when it hands over
    // nothing.
    const candidates = entities?.length ? entities : Object.keys(hass.entities);

    for (const entityId of candidates) {
      const entry = hass.entities[entityId];
      if (entry?.platform === 'bergfex' && entry.device_id) return entry.device_id;
    }
    return undefined;
  }

  /**
   * How tall the card is in a masonry column, in rows of roughly 50px.
   *
   * Derived from the resorts rather than fixed, or masonry packs the column
   * against the height of a one-resort card.
   */
  public getCardSize(): number {
    const resorts = this._config?.resorts?.length ?? 0;
    if (resorts === 0) return 1;

    // Header, then per resort: the name and status line, plus whichever
    // sections are switched on.
    let perResort = 2;
    if (this._config.show_snow) perResort += 1;
    if (this._config.show_lifts_slopes) perResort += 1;
    if (this._config.show_trails) perResort += 1;
    if (this._config.show_conditions) perResort += this._config.conditions_default_open ? 2 : 1;
    if (this._config.show_forecast) perResort += this._config.forecast_default_open ? 3 : 1;

    return 1 + resorts * perResort;
  }

  /**
   * How the card asks to be placed on a sections dashboard.
   *
   * Without this a section gives every custom card the same default box.
   *
   * `rows: 'auto'` rather than `getCardSize()`: that is a masonry number, and a
   * hand-maintained model of the layout that cannot know what the card leaves
   * out. Home Assistant measures the rendered card instead. `getCardSize()`
   * remains for masonry, which has no auto.
   */
  public getGridOptions(): LovelaceGridOptions {
    return { columns: 'full', min_columns: 6, rows: 'auto', min_rows: 2 };
  }

  private _getResorts(hass: HomeAssistant, config: BergfexCardConfig): Record<string, Resort> {
    const resorts: Record<string, Resort> = {};

    const allEntities = Object.values(hass.states);

    config.resorts.forEach((resort: ResortConfig) => {
      if (!resort) return;
      // The editor now stores device IDs as strings.
      // We still support the object format for manual YAML configuration.
      const deviceId = typeof resort === 'string' ? resort : resort.device;
      const customName = typeof resort === 'object' ? resort.name : undefined;

      const resolved = resolveResort(hass, deviceId);
      if (!resolved.ok) {
        // Keep the resort in the list rather than dropping it. Dropping it is
        // what made an unknown device render as an empty card, with nothing to
        // tell the user which of their resorts had gone missing.
        resorts[deviceId] = { problem: resolved.problem, name: customName };
        return;
      }
      const deviceEntities = resolved.value.entities;

      // Use the device_id as the unique key for the resort.
      if (!resorts[deviceId]) {
        resorts[deviceId] = {
          forecast_days: [],
          forecast_summaries: [],
        };
      }

      if (customName) {
        resorts[deviceId].name = customName;
      }

      deviceEntities.forEach((entity) => {
        const entityId = entity.entity_id;
        if (entityId.endsWith('_operation_status')) resorts[deviceId].operation_status = entityId;
        else if (entityId.endsWith('_status')) {
          resorts[deviceId].status = entityId;
          // Check if this is a cross-country resort based on the status entity
          const link = entity.attributes?.link as string | undefined;
          const icon = entity.attributes?.icon as string | undefined;
          if (
            (link && link.includes('/langlaufen/')) ||
            icon === 'mdi:ski-cross-country' ||
            icon === 'mdi:ski-cross-country-skating'
          ) {
            resorts[deviceId].is_cross_country = true;
          }
        }
        if (entityId.endsWith('_snow_valley')) resorts[deviceId].snow_valley = entityId;
        if (entityId.endsWith('_snow_mountain')) resorts[deviceId].snow_mountain = entityId;
        if (entityId.endsWith('_new_snow')) resorts[deviceId].new_snow = entityId;
        if (entityId.endsWith('_lifts_open_count')) resorts[deviceId].lifts_open_count = entityId;
        else if (entityId.endsWith('_lifts_open') && !resorts[deviceId].lifts_open_count)
          resorts[deviceId].lifts_open = entityId;
        if (entityId.endsWith('_last_update')) resorts[deviceId].last_update = entityId;
        if (entityId.endsWith('_snow_condition')) resorts[deviceId].snow_condition = entityId;
        if (entityId.endsWith('_last_snowfall')) resorts[deviceId].last_snowfall = entityId;
        if (entityId.endsWith('_avalanche_warning')) resorts[deviceId].avalanche_warning = entityId;
        if (entityId.endsWith('_slopes_open_km')) resorts[deviceId].slopes_open_km = entityId;
        if (entityId.endsWith('_slopes_open_count')) resorts[deviceId].slopes_open_count = entityId;
        else if (entityId.endsWith('_slopes_open') && !resorts[deviceId].slopes_open_count)
          resorts[deviceId].slopes_open = entityId;
        if (entityId.endsWith('_slope_condition')) resorts[deviceId].slope_condition = entityId;
        if (entityId.endsWith('_classical_open_km')) resorts[deviceId].classical_trails_open = entityId;
        if (entityId.endsWith('_skating_open_km')) resorts[deviceId].skating_trails_open = entityId;
        if (entityId.endsWith('_classical_condition')) resorts[deviceId].classical_condition = entityId;
        if (entityId.endsWith('_skating_condition')) resorts[deviceId].skating_condition = entityId;
        // If explicit total sensors exist (older setups), keep them; otherwise totals may be provided as attributes

        if (entityId.includes('_forecast_image_day_')) {
          resorts[deviceId].forecast_days?.push(entityId);
        }
        if (entityId.includes('_summary_image_')) {
          resorts[deviceId].forecast_summaries?.push(entityId);
        }
      });

      // `hass` rather than `this.hass`: shouldUpdate calls this with the
      // previous state to compare against, and reading the current one there
      // would judge the old entities by the new states.
      resorts[deviceId].forecast_days = this._usableForecastImages(hass, resorts[deviceId].forecast_days, /day_(\d+)/);
      resorts[deviceId].forecast_summaries = this._usableForecastImages(
        hass,
        resorts[deviceId].forecast_summaries,
        /summary_image_(\d+)h/,
      );

      // Sort forecast arrays
      resorts[deviceId].forecast_days?.sort();
      resorts[deviceId].forecast_summaries?.sort((a, b) => {
        // Sort by hour number in the entity ID (e.g. ...summary_image_48h).
        // This read `/summary_(\d+)h/`, which never matches: the digits follow
        // "summary_image_", not "summary_". Every id scored 0, so the sort was
        // a no-op that happened to look right while the entities arrived in
        // creation order.
        const getHour = (id: string) => {
          const match = id.match(/summary_image_(\d+)h/);
          return match ? parseInt(match[1], 10) : 0;
        };
        return getHour(a) - getHour(b);
      });

      // Fallback: If no forecast images found via device ID, try to find them by pattern matching
      if (
        (!resorts[deviceId].forecast_days || resorts[deviceId].forecast_days.length === 0) &&
        (!resorts[deviceId].forecast_summaries || resorts[deviceId].forecast_summaries.length === 0)
      ) {
        // Construct a search pattern based on the resort name or ID if possible.
        // Since we don't have the slug readily available, we can try to match the pattern of other entities.
        // Example entity: sensor.resort_slug_status -> image.resort_slug_snow_forecast_day_0
        const statusEntity = resorts[deviceId].status;
        if (statusEntity) {
          const slugMatch = statusEntity.match(/^sensor\.(.+)_status$/);
          if (slugMatch) {
            const slug = slugMatch[1];
            const forecastPattern = `image.${slug}_snow_forecast`;

            allEntities.forEach((entity) => {
              if (entity.entity_id.startsWith(forecastPattern)) {
                if (entity.entity_id.includes('_day_')) {
                  resorts[deviceId].forecast_days?.push(entity.entity_id);
                } else if (entity.entity_id.includes('_summary_')) {
                  resorts[deviceId].forecast_summaries?.push(entity.entity_id);
                }
              }
            });

            // Sort again after fallback
            resorts[deviceId].forecast_days?.sort();
            resorts[deviceId].forecast_summaries?.sort((a, b) => {
              const getHour = (id: string) => {
                const match = id.match(/summary_(\d+)h/);
                return match ? parseInt(match[1], 10) : 0;
              };
              return getHour(a) - getHour(b);
            });
          }
        }
      }
    });

    return resorts;
  }

  protected shouldUpdate(changedProperties: Map<string | number | symbol, unknown>): boolean {
    // Before any early return: this method sees every update, and the ones it
    // declines to render are exactly the ones `updated` would never hear about.
    this._refreshTrendBaseline();

    if (changedProperties.has('_config')) {
      return true;
    }

    const oldHass = changedProperties.get('hass') as HomeAssistant | undefined;
    if (oldHass) {
      // Watch the union of before and after. Deriving the list from the new state
      // alone meant that when a resort's entities disappeared - a reload, a restart,
      // a failed refresh - nothing was left to compare, so the card skipped the
      // update and kept presenting the last known snow depths as current.
      const entitiesOf = (hass: HomeAssistant) =>
        Object.values(this._getResorts(hass, this._config)).flatMap((s) => Object.values(s));
      const watched = new Set<string>();
      for (const entity of [...entitiesOf(this.hass), ...entitiesOf(oldHass)]) {
        if (typeof entity === 'string') watched.add(entity);
      }

      const hasChanged = [...watched].some((entity) => oldHass.states[entity] !== this.hass.states[entity]);

      // Not just `language`: dates format against `locale.language` and numbers
      // against `locale.number_format`, so a locale-only profile change has to
      // re-render too.
      const localeChanged =
        oldHass.language !== this.hass.language ||
        oldHass.locale?.language !== this.hass.locale?.language ||
        oldHass.locale?.number_format !== this.hass.locale?.number_format ||
        oldHass.locale?.time_format !== this.hass.locale?.time_format;

      return hasChanged || localeChanged || changedProperties.has('_historyState');
    }

    return true; // First render
  }

  /** The entities whose value 24 hours ago the trend arrows are drawn from. */
  private _trendEntities(): string[] {
    if (!this.hass || !this._config?.resorts) return [];

    const resorts = this._getResorts(this.hass, this._config);
    return Object.values(resorts)
      .flatMap((r) => [
        r.snow_mountain,
        r.snow_valley,
        r.new_snow,
        r.lifts_open_count,
        r.lifts_open,
        r.slopes_open_km,
        r.slopes_open_count,
        r.slopes_open,
        r.classical_trails_open,
        r.skating_trails_open,
      ])
      .filter(Boolean) as string[];
  }

  /**
   * Fetch the 24-hour-old baseline, but only when it would answer differently.
   *
   * Home Assistant hands every card a new `hass` whenever any entity in the
   * instance changes, so keying off that alone asked the recorder several times
   * a second. Key it on what the answer depends on instead: the entities
   * compared, their current values, and the hour - the 24-hour window slides
   * even when nothing on the page moves.
   */
  private _refreshTrendBaseline(): void {
    if (!this.hass || !this._config?.show_trend) {
      this._trendBaselineKey = undefined;
      return;
    }

    const entities = this._trendEntities();
    if (entities.length === 0) return;

    const hour = Math.floor(Date.now() / 3_600_000);
    const key = `${hour}|${entities.map((id) => `${id}=${this.hass.states[id]?.state}`).join('|')}`;
    if (key === this._trendBaselineKey) return;

    this._trendBaselineKey = key;
    this._fetchHistory(entities);
  }

  private async _fetchHistory(entities: string[]): Promise<void> {
    this._historyState = await fetchHistory(this.hass, entities, 24);
  }

  /** Which way a value moved over the last 24 hours, when that is known. */
  private _trendOf(entityId: string, currentState: string): Trend | undefined {
    if (!this._config.show_trend) return undefined;
    const oldState = this._historyState[entityId];
    if (oldState === undefined || this._isNA(currentState) || this._isNA(oldState)) return undefined;

    const currentVal = parseFloat(currentState);
    const oldVal = parseFloat(oldState);

    if (isNaN(currentVal) || isNaN(oldVal)) return undefined;

    if (currentVal > oldVal) return 'up';
    if (currentVal < oldVal) return 'down';
    return 'same';
  }

  /**
   * The trend arrow. Hidden from screen readers: colour and shape are all it
   * has, so the item it sits in says the same thing in words instead.
   */
  private _renderTrend(entityId: string, currentState: string): TemplateResult {
    const trend = this._trendOf(entityId, currentState);
    if (!trend) return html``;

    const icon = { up: 'mdi:trending-up', down: 'mdi:trending-down', same: 'mdi:trending-neutral' }[trend];
    return html`<ha-icon class="trend-icon ${trend}" icon=${icon} aria-hidden="true"></ha-icon>`;
  }

  private _handleMoreInfo(entityId: string): void {
    fireEvent(this, 'hass-more-info', { entityId });
  }

  private _handleTabChange(resortId: string, tab: ForecastTab, e: Event): void {
    e.stopPropagation();
    this._forecastState = {
      ...this._forecastState,
      [resortId]: {
        ...this._forecastState[resortId],
        tab,
        index: 0, // Reset index when switching tabs
      },
    };
  }

  /**
   * Arrow keys, Home and End move between the forecast tabs, as in any tab list.
   * Tab itself leaves the list: only the selected tab is in the tab order.
   */
  private _handleTabKeydown(resortId: string, tabs: ForecastTab[], tab: ForecastTab, e: KeyboardEvent): void {
    const current = tabs.indexOf(tab);
    let next: number;
    switch (e.key) {
      case 'ArrowRight':
        next = (current + 1) % tabs.length;
        break;
      case 'ArrowLeft':
        next = (current - 1 + tabs.length) % tabs.length;
        break;
      case 'Home':
        next = 0;
        break;
      case 'End':
        next = tabs.length - 1;
        break;
      default:
        return;
    }
    e.preventDefault();
    if (tabs[next] !== tab) this._handleTabChange(resortId, tabs[next], e);

    const id = this._domId(resortId, `tab-${tabs[next]}`);
    this.updateComplete.then(() => this.shadowRoot?.getElementById(id)?.focus());
  }

  private _handleCarouselChange(resortId: string, direction: 'prev' | 'next', length: number, e: Event): void {
    e.stopPropagation();
    const currentState = this._forecastState[resortId] || { tab: 'daily', index: 0 };
    let newIndex = currentState.index + (direction === 'next' ? 1 : -1);

    if (newIndex < 0) newIndex = length - 1;
    if (newIndex >= length) newIndex = 0;

    this._forecastState = {
      ...this._forecastState,
      [resortId]: {
        ...currentState,
        index: newIndex,
      },
    };
  }

  private _toggleAccordion(resortId: string, section: 'conditions' | 'forecast', e: Event): void {
    e.stopPropagation();
    const resortState = this._accordionState[resortId] || {};
    const isOpen = resortState[section] ?? this._config[`${section}_default_open` as keyof BergfexCardConfig] ?? false;
    this._accordionState = {
      ...this._accordionState,
      [resortId]: {
        ...resortState,
        [section]: !isOpen,
      },
    };
  }

  /**
   * Drop forecast images that cannot render, and keep one per day or interval.
   *
   * Where an install carries rows from more than one unique id scheme, the
   * superseded ones sit on the same device with nothing behind them, and the
   * carousel collected twice as many images.
   *
   * Matched on `restored`, not `unavailable`: a resort whose coordinator is
   * failing is unavailable too, and that is worth showing. The states come off
   * the `hass` passed in, because shouldUpdate also calls this with the old one.
   */
  private _usableForecastImages(hass: HomeAssistant, entityIds: string[] | undefined, key: RegExp): string[] {
    if (!entityIds) return [];

    const live = entityIds.filter((id) => {
      const state = hass.states[id];
      return state !== undefined && !(state.state === 'unavailable' && state.attributes?.restored);
    });

    // Should two survive for the same day - neither of them restored - prefer
    // the plain entity id over the "_2" Home Assistant appends on a collision,
    // which is what sorting first settles.
    const seen = new Set<string>();
    return [...live].sort().filter((id) => {
      const slot = id.match(key)?.[1];
      if (slot === undefined) return true;
      if (seen.has(slot)) return false;
      seen.add(slot);
      return true;
    });
  }

  private _formatForecastDate(dayOffset: number): string {
    const date = new Date();
    date.setDate(date.getDate() + dayOffset);

    if (dayOffset === 0) {
      return localize(this.hass, 'component.bergfex-card.card.forecast.today');
    } else if (dayOffset === 1) {
      return localize(this.hass, 'component.bergfex-card.card.forecast.tomorrow');
    } else {
      // Intl knows each locale's order and separator; hand-assembling "02.12."
      // printed the German order at everyone. The month is named because an
      // all-numeric "12/04" reads both ways, matching the season teaser.
      const locale = this.hass.locale?.language || this.hass.language || 'en';
      return date.toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' });
    }
  }

  private _renderProgressBar(value: number, total: number): TemplateResult {
    const percentage = Math.min(100, Math.max(0, (value / total) * 100));
    return html`
      <span class="progress-bar-container">
        <span class="progress-bar-fill" style="width: ${percentage}%"></span>
      </span>
    `;
  }

  /**
   * Whether a state carries no report at all.
   *
   * bergfex writes it in the language the resort was set up in, and Home
   * Assistant has its own two words for it.
   */
  private _isNA(state: string): boolean {
    return NO_REPORT_STATES.includes(state?.trim().toLowerCase());
  }

  /**
   * Resolve the badge shown next to a resort name.
   *
   * "Open" stays the operational state. Naming the running period instead of
   * collapsing everything else into a red "Closed" tells the user why there is
   * no snow report.
   */
  private _statusBadge(state: string, attrs: Record<string, unknown>): { key: string; variant: string } {
    if ((state || '').toLowerCase() === 'open') return { key: 'open', variant: 'open' };

    const today = new Date().toISOString().slice(0, 10);
    const inPeriod = (season: 'winter' | 'summer') => {
      const start = attrs[`${season}_season_start`] as string | undefined;
      const end = attrs[`${season}_season_end`] as string | undefined;
      return Boolean(start && end && start <= today && today <= end);
    };

    if (inPeriod('winter')) return { key: 'winter_season', variant: 'winter-season' };
    if (inPeriod('summer')) return { key: 'summer_season', variant: 'summer-season' };
    if ((state || '').toLowerCase() === 'closed') return { key: 'closed', variant: 'closed' };
    return { key: 'unknown', variant: '' };
  }

  /**
   * A short "from 05.12." hint for resorts whose winter season has not started.
   *
   * Shown wherever the winter season is still ahead - both under a summer badge
   * and under a plain closed one - because between the seasons the card is at its
   * least informative and the date is the one thing a user actually wants.
   */
  private _winterTeaser(attrs: Record<string, unknown>): string | undefined {
    const start = attrs.winter_season_start as string | undefined;
    if (!start) return undefined;

    const today = new Date().toISOString().slice(0, 10);
    const end = attrs.winter_season_end as string | undefined;

    // Nothing to tease while the season is running.
    if (start <= today && (!end || today <= end)) return undefined;

    const date = new Date(`${start}T00:00:00`);
    if (Number.isNaN(date.getTime())) return undefined;

    // "ab 12/04" reads as April or December depending on the reader, and a season
    // start is not guessable from context, so the month is named.
    const locale = this.hass.locale?.language || this.hass.language || 'en';
    const formatted = new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'short',
    }).format(date);

    if (start > today) {
      return localize(this.hass, 'component.bergfex-card.card.status.season_from', { date: formatted });
    }

    // The start has passed, which through summer means bergfex is still showing
    // last season's dates - it publishes the new ones during autumn. Resorts open
    // at close to the same date every year, so quoting it is useful, but it is an
    // estimate and has to say so rather than pose as this year's date.
    const monthsAgo = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24 * 30.44);
    if (monthsAgo > 18) return undefined;

    return localize(this.hass, 'component.bergfex-card.card.status.season_last_year', { date: formatted });
  }

  /**
   * Whether a resort is genuinely shut, as opposed to merely not skiable today.
   *
   * A resort in summer operation is not closed - bergfex reports it as
   * "Sommerbetrieb" and it may well be running lifts.
   */
  private _isOutOfSeason(resort: Resort): boolean {
    const state = resort.status ? this.hass.states[resort.status] : undefined;
    if (!state) return true;
    if (state.state.toLowerCase() === 'open') return false;

    return this._statusBadge(state.state, state.attributes ?? {}).variant === 'closed';
  }

  private _conditionText(state: string): string {
    return this._isNA(state) ? localize(this.hass, 'component.bergfex-card.card.status.unknown') : state;
  }

  private _isCrossCountryResort(resort: Resort): boolean {
    return !!(
      resort.is_cross_country ||
      resort.classical_trails_open ||
      resort.skating_trails_open ||
      resort.classical_condition ||
      resort.skating_condition
    );
  }

  /**
   * An id for an element of one resort, unique within the card's shadow root.
   *
   * The ARIA references between a heading and its resort, or a tab and its
   * panel, need ids; the resort key is a device id from the config, so anything
   * an id should not carry is replaced.
   */
  private _domId(resortId: string, part: string): string {
    return `bergfex-${resortId.replace(/[^A-Za-z0-9_-]/g, '_')}-${part}`;
  }

  /**
   * The drawn value of a numeric item, and the words for it.
   *
   * With a usable `total` it reads "open/total" and draws a progress bar; a
   * total that is not a number falls back to the open figure alone.
   */
  private _numericValue(
    entity: HassEntity | undefined,
    unit?: string,
    total?: unknown,
  ): Pick<DetailItem, 'value' | 'valueText'> {
    if (!entity || isNaN(parseFloat(entity.state))) {
      return {
        value: html`<span>N/A</span>`,
        valueText: localize(this.hass, 'component.bergfex-card.card.a11y.not_available'),
      };
    }

    const suffix = unit ? ` ${unit}` : '';
    const trend = this._renderTrend(entity.entity_id, entity.state);
    const openVal = parseFloat(entity.state);
    const totalVal = total ? parseFloat(String(total)) : NaN;

    if (!isNaN(totalVal)) {
      const open = formatNumber(openVal, this.hass);
      const all = formatNumber(totalVal, this.hass);
      return {
        value: html`<span class="value-row"><span>${open}/${all}${suffix}</span>${trend}</span>
          ${this._renderProgressBar(openVal, totalVal)}`,
        valueText: localize(this.hass, 'component.bergfex-card.card.a11y.of_total', {
          open,
          total: `${all}${suffix}`,
        }),
      };
    }

    const value = `${formatNumber(entity.state, this.hass)}${suffix}`;
    return { value: html`<span class="value-row"><span>${value}</span>${trend}</span>`, valueText: value };
  }

  /**
   * One figure in the resort grid, as a list item holding a button.
   *
   * The button opens the entity's more-info dialog. Its accessible name puts
   * the label first and says the trend in words - drawn, the value sits above
   * its label and the trend is only a coloured arrow.
   */
  private _renderDetailItem(item: DetailItem): TemplateResult {
    const trend = item.entity ? this._trendOf(item.entity.entity_id, item.entity.state) : undefined;
    const valueText = trend
      ? `${item.valueText}, ${localize(this.hass, `component.bergfex-card.card.a11y.trend_${trend}`)}`
      : item.valueText;
    const name = localize(this.hass, 'component.bergfex-card.card.a11y.value', {
      label: item.name,
      value: valueText,
    });

    return html`<li class="detail-cell">
      <button
        type="button"
        class=${classMap({ 'detail-item': true, 'n-a': item.na })}
        aria-label=${name}
        aria-disabled=${item.entity ? nothing : 'true'}
        @click=${(e: Event) => {
          e.stopPropagation();
          if (item.entity) this._handleMoreInfo(item.entity.entity_id);
          item.onClick?.(e);
        }}
      >
        ${item.icon}
        <span class="detail-item-value">
          ${item.value}
          <span class="detail-item-label">${item.label}</span>
        </span>
      </button>
    </li>`;
  }

  /** A text report from the conditions section, such as the snow condition. */
  private _renderConditionItem(entity: HassEntity, icon: TemplateResult, labelKey: string): TemplateResult {
    const text = this._conditionText(entity.state);
    const label = localize(this.hass, `component.bergfex-card.card.header.${labelKey}`);
    return this._renderDetailItem({
      entity,
      na: this._isNA(entity.state),
      icon,
      value: html`<span>${text}</span>`,
      valueText: text,
      label,
      name: label,
    });
  }

  protected render(): TemplateResult {
    if (!this._config) {
      return html``;
    }

    // The picker previews the card without hass and without a resort. Render the
    // empty card with the hint instead of nothing, so the preview tile shows
    // what the card is rather than a blank box.
    if (!this.hass || this._config.resorts.length === 0) {
      return html`
        <ha-card .header=${this._config.title}>
          <div class="card-content">
            <div class="warning">${localize(this.hass, 'common.errors.no_resorts')}</div>
          </div>
        </ha-card>
      `;
    }

    let resortEntries = Object.entries(this._getResorts(this.hass, this._config));

    if (this._config.hide_closed_resorts) {
      resortEntries = resortEntries.filter(([, r]) => !this._isOutOfSeason(r));
    }

    const sortBy = this._config.sort_by;
    if (sortBy && sortBy !== 'none') {
      resortEntries.sort(([, a], [, b]) => {
        let valA: number | string | undefined;
        let valB: number | string | undefined;

        switch (sortBy) {
          case 'mountain':
            if (this._isCrossCountryResort(a) || this._isCrossCountryResort(b)) break; // Skip for cross-country
            valA = a.snow_mountain ? parseFloat(this.hass.states[a.snow_mountain].state) : NaN;
            valB = b.snow_mountain ? parseFloat(this.hass.states[b.snow_mountain].state) : NaN;
            break;
          case 'valley':
            if (this._isCrossCountryResort(a) || this._isCrossCountryResort(b)) break; // Skip for cross-country
            valA = a.snow_valley ? parseFloat(this.hass.states[a.snow_valley].state) : NaN;
            valB = b.snow_valley ? parseFloat(this.hass.states[b.snow_valley].state) : NaN;
            break;
          case 'new':
            if (this._isCrossCountryResort(a) || this._isCrossCountryResort(b)) break; // Skip for cross-country
            valA = a.new_snow ? parseFloat(this.hass.states[a.new_snow].state) : NaN;
            valB = b.new_snow ? parseFloat(this.hass.states[b.new_snow].state) : NaN;
            break;
          case 'lift': {
            if (this._isCrossCountryResort(a) || this._isCrossCountryResort(b)) break; // Skip for cross-country
            // `lifts_open` is only mapped when `lifts_open_count` is absent, so
            // reading it alone left every resort at NaN and the sort did nothing.
            // Mirror what the card renders, which prefers the count.
            const liftsOf = (r: Resort) => {
              const entity = r.lifts_open_count ?? r.lifts_open;
              return entity ? parseFloat(this.hass.states[entity]?.state ?? '') : NaN;
            };
            valA = liftsOf(a);
            valB = liftsOf(b);
            break;
          }
          case 'classical':
            valA = a.classical_trails_open ? parseFloat(this.hass.states[a.classical_trails_open].state) : NaN;
            valB = b.classical_trails_open ? parseFloat(this.hass.states[b.classical_trails_open].state) : NaN;
            break;
          case 'skating':
            valA = a.skating_trails_open ? parseFloat(this.hass.states[a.skating_trails_open].state) : NaN;
            valB = b.skating_trails_open ? parseFloat(this.hass.states[b.skating_trails_open].state) : NaN;
            break;
          case 'update': {
            // Resorts without a usable timestamp sort last rather than scrambling
            // the order through NaN comparisons.
            const timeA = parseDate(a.last_update ? this.hass.states[a.last_update]?.state : undefined)?.getTime();
            const timeB = parseDate(b.last_update ? this.hass.states[b.last_update]?.state : undefined)?.getTime();
            if (timeA === undefined && timeB === undefined) return 0;
            if (timeA === undefined) return 1;
            if (timeB === undefined) return -1;
            return timeB - timeA; // Newest first
          }
        }

        if (typeof valA === 'number' && typeof valB === 'number') {
          const aIsNaN = isNaN(valA);
          const bIsNaN = isNaN(valB);

          if (aIsNaN && bIsNaN) return 0;
          if (aIsNaN) return 1; // Push invalid 'a' to the end
          if (bIsNaN) return -1; // Push invalid 'b' to the end

          return valB - valA; // Sort descending
        }
        return 0;
      });
    }

    return html`
      <ha-card .header=${this._config.title}>
        <div class="card-content">
          ${resortEntries.map(([resortId, resort]) => {
            const primaryEntity = resort.status;
            if (resort.problem || !primaryEntity) {
              // A resort that resolved but has no status sensor is reporting
              // nothing usable, which is the same story for the reader as a
              // device that is not there at all.
              const problem: ResolutionProblem = resort.problem ?? {
                reason: 'unavailable',
                subject: resort.name ?? resortId,
              };
              return html` <div class="warning">${problemMessage(this.hass, problem)}</div> `;
            }

            const device = this.hass.devices[resortId];

            const resortName = resort.name || device?.name_by_user || device?.name || 'Unknown Resort';

            const operation_status = resort.operation_status ? this.hass.states[resort.operation_status] : undefined;
            const statusState = resort.status ? this.hass.states[resort.status] : undefined;
            const statusRaw = (statusState?.state as string) ?? 'unknown';
            const status = statusRaw;
            const badge = this._statusBadge(statusRaw, statusState?.attributes ?? {});
            const winterTeaser = this._winterTeaser(statusState?.attributes ?? {});
            const statusLabel = localize(this.hass, `component.bergfex-card.card.status.${badge.key}`) || status;
            const link = statusState?.attributes.link as string | undefined;
            const snow_valley = resort.snow_valley ? this.hass.states[resort.snow_valley] : undefined;
            const snow_mountain = resort.snow_mountain ? this.hass.states[resort.snow_mountain] : undefined;
            const new_snow = resort.new_snow ? this.hass.states[resort.new_snow] : undefined;
            const lifts_open_count = resort.lifts_open_count ? this.hass.states[resort.lifts_open_count] : undefined;
            // Fallback to lifts_open if lifts_open_count is not defined
            const lifts_open_entity = lifts_open_count
              ? lifts_open_count
              : resort.lifts_open
                ? this.hass.states[resort.lifts_open]
                : undefined;
            const last_update = resort.last_update ? this.hass.states[resort.last_update] : undefined;
            // Not every resort publishes a timestamp; without this the footer
            // renders a clock next to the string "Invalid Date".
            const last_update_at = parseDate(last_update?.state);
            const snow_condition = resort.snow_condition ? this.hass.states[resort.snow_condition] : undefined;
            const slope_condition = resort.slope_condition ? this.hass.states[resort.slope_condition] : undefined;
            const last_snowfall = resort.last_snowfall ? this.hass.states[resort.last_snowfall] : undefined;
            const avalanche_warning = resort.avalanche_warning ? this.hass.states[resort.avalanche_warning] : undefined;
            const slopes_open_km = resort.slopes_open_km ? this.hass.states[resort.slopes_open_km] : undefined;
            const slopes_open_count = resort.slopes_open_count ? this.hass.states[resort.slopes_open_count] : undefined;
            // Fallback to slopes_open if slopes_open_count is not defined
            const slopes_open_entity = slopes_open_count
              ? slopes_open_count
              : resort.slopes_open
                ? this.hass.states[resort.slopes_open]
                : undefined;

            const classical_open_km = resort.classical_trails_open
              ? this.hass.states[resort.classical_trails_open]
              : undefined;
            const skating_open_km = resort.skating_trails_open
              ? this.hass.states[resort.skating_trails_open]
              : undefined;
            const classical_condition = resort.classical_condition
              ? this.hass.states[resort.classical_condition]
              : undefined;
            const skating_condition = resort.skating_condition ? this.hass.states[resort.skating_condition] : undefined;

            const isCrossCountry = this._isCrossCountryResort(resort);

            // Extract totals for cross-country if provided as attributes or as separate sensors
            const classical_total = classical_open_km?.attributes?.total;
            const skating_total = skating_open_km?.attributes?.total;
            // Lifts and slopes: totals may be provided as attributes on the "open" sensor
            const lifts_total = lifts_open_entity?.attributes?.total;

            const slopes_total_km = slopes_open_km?.attributes?.total;

            const slopes_total = slopes_open_entity?.attributes?.total;
            const isConditionsOpen =
              this._accordionState[resortId]?.['conditions'] ?? this._config.conditions_default_open;
            const isForecastOpen = this._accordionState[resortId]?.['forecast'] ?? this._config.forecast_default_open;

            // The resort is an article named by its heading. Its click opens the
            // status; the button in the heading has no handler of its own - its
            // click bubbles up to that one - and is there so the keyboard can
            // reach the status too, which a focusable div never let it.
            const nameId = this._domId(resortId, 'name');
            const noValue = (entity?: HassEntity) => !entity || isNaN(parseFloat(entity.state));
            const header = (key: string) => localize(this.hass, `component.bergfex-card.card.header.${key}`);
            const spoken = (key: string) => localize(this.hass, `component.bergfex-card.card.a11y.${key}`);
            // The visible label squeezes the elevation into "(2100m)"; spelled with
            // a space, a screen reader says "metres" rather than the letter m.
            const withElevation = (label: string, entity?: HassEntity) =>
              entity?.attributes.elevation ? `${label} (${entity.attributes.elevation} m)` : label;
            const elevation = (entity?: HassEntity) =>
              entity?.attributes.elevation ? `(${entity.attributes.elevation}m)` : '';
            const linkTitle = localize(this.hass, 'component.bergfex-card.card.header.link_title', { resortName });

            return html`
              <article class="resort" aria-labelledby=${nameId} @click=${() => this._handleMoreInfo(primaryEntity)}>
                <div class="resort-header">
                  <!-- prettier-ignore -->
                  <h2 class="resort-name" id=${nameId}><button type="button" class="resort-name-button">${resortName}</button></h2>
                  <div class="resort-status-group">
                    <span class="visually-hidden">${spoken('status_prefix')}</span>
                    <span
                      class=${classMap({
                        'resort-status': true,
                        [badge.variant]: Boolean(badge.variant),
                      })}
                      >${statusLabel}</span
                    >
                    ${winterTeaser ? html`<span class="season-teaser">${winterTeaser}</span>` : ''}
                  </div>
                </div>

                <ul class=${isCrossCountry ? 'details cross-country-details' : 'details'} role="list">
                  ${
                    this._config.show_snow && !isCrossCountry
                      ? html`
                          ${this._renderDetailItem({
                            entity: snow_mountain,
                            na: noValue(snow_mountain),
                            icon: html`<span class="custom-icon stroke" aria-hidden="true"
                              >${unsafeSVG(mountainIcon)}</span
                            >`,
                            ...this._numericValue(snow_mountain, snow_mountain?.attributes.unit_of_measurement),
                            label: html`${header('snow_mountain')} ${elevation(snow_mountain)}`,
                            name: withElevation(spoken('snow_mountain'), snow_mountain),
                          })}
                          ${this._renderDetailItem({
                            entity: snow_valley,
                            na: noValue(snow_valley),
                            icon: html`<span class="custom-icon stroke" aria-hidden="true"
                              >${unsafeSVG(valleyIcon)}</span
                            >`,
                            ...this._numericValue(snow_valley, snow_valley?.attributes.unit_of_measurement),
                            label: html`${header('snow_valley')} ${elevation(snow_valley)}`,
                            name: withElevation(spoken('snow_valley'), snow_valley),
                            onClick: (e: Event) => {
                              // Highlight the clicked element
                              const target = e.currentTarget as HTMLElement;
                              target.classList.add('clicked');
                              setTimeout(() => {
                                target.classList.remove('clicked');
                              }, 500);
                            },
                          })}
                          ${this._renderDetailItem({
                            entity: new_snow,
                            na: noValue(new_snow),
                            icon: html`<ha-icon icon="mdi:weather-snowy-heavy" aria-hidden="true"></ha-icon>`,
                            ...this._numericValue(new_snow, new_snow?.attributes.unit_of_measurement),
                            label: header('new_snow'),
                            name: spoken('new_snow'),
                          })}
                        `
                      : ''
                  }
                  ${
                    isCrossCountry && this._config.show_trails
                      ? html`
                          ${
                            classical_open_km
                              ? this._renderDetailItem({
                                  entity: classical_open_km,
                                  na: noValue(classical_open_km),
                                  icon: html`<span class="custom-icon fill" aria-hidden="true"
                                    >${unsafeSVG(classicCrossCountryIcon)}</span
                                  >`,
                                  ...this._numericValue(
                                    classical_open_km,
                                    classical_open_km.attributes.unit_of_measurement ?? 'km',
                                    classical_total,
                                  ),
                                  label: header('classical_trails'),
                                  name: header('classical_trails'),
                                })
                              : ''
                          }
                          ${
                            skating_open_km
                              ? this._renderDetailItem({
                                  entity: skating_open_km,
                                  na: noValue(skating_open_km),
                                  icon: html`<span class="custom-icon fill" aria-hidden="true"
                                    >${unsafeSVG(skatingCrossCountryIcon)}</span
                                  >`,
                                  ...this._numericValue(
                                    skating_open_km,
                                    skating_open_km.attributes.unit_of_measurement ?? 'km',
                                    skating_total,
                                  ),
                                  label: header('skating_trails'),
                                  name: header('skating_trails'),
                                })
                              : ''
                          }
                        `
                      : html`
                          ${
                            this._config.show_lifts_slopes && lifts_open_entity
                              ? this._renderDetailItem({
                                  entity: lifts_open_entity,
                                  na: noValue(lifts_open_entity),
                                  icon: html`<ha-icon icon="mdi:gondola" aria-hidden="true"></ha-icon>`,
                                  ...this._numericValue(lifts_open_entity, undefined, lifts_total),
                                  label: localize(this.hass, 'component.bergfex-card.card.lifts_open'),
                                  name: localize(this.hass, 'component.bergfex-card.card.lifts_open'),
                                })
                              : ''
                          }
                          ${
                            this._config.show_lifts_slopes && slopes_open_km
                              ? this._renderDetailItem({
                                  entity: slopes_open_km,
                                  na: noValue(slopes_open_km),
                                  icon: html`<span class="custom-icon stroke" aria-hidden="true">
                                    <ha-icon icon="mdi:slope-downhill"></ha-icon>
                                  </span>`,
                                  ...this._numericValue(
                                    slopes_open_km,
                                    slopes_open_km.attributes.unit_of_measurement ?? 'km',
                                    slopes_total_km,
                                  ),
                                  label: header('slopes_info_km'),
                                  name: header('slopes_info_km'),
                                })
                              : ''
                          }
                          ${
                            this._config.show_lifts_slopes && slopes_open_entity
                              ? (() => {
                                  // With a total the label says so, and a total that is
                                  // not a number greys the item out like a missing value.
                                  const label = slopes_total
                                    ? `${header('slopes_info')} (${header('slopes_total')})`
                                    : header('slopes_info');
                                  return this._renderDetailItem({
                                    entity: slopes_open_entity,
                                    na:
                                      noValue(slopes_open_entity) ||
                                      (Boolean(slopes_total) && isNaN(parseFloat(String(slopes_total)))),
                                    icon: html`<ha-icon icon="mdi:counter" aria-hidden="true"></ha-icon>`,
                                    ...this._numericValue(slopes_open_entity, undefined, slopes_total),
                                    label,
                                    name: label,
                                  });
                                })()
                              : ''
                          }
                        `
                  }
                </ul>

                ${
                  this._config.show_conditions &&
                  (snow_condition ||
                    slope_condition ||
                    avalanche_warning ||
                    last_snowfall ||
                    operation_status ||
                    classical_condition ||
                    skating_condition)
                    ? html`
                        <div class="accordion-container">
                          <h3 class="accordion-title">
                            <button
                              type="button"
                              class="accordion-header"
                              aria-expanded=${isConditionsOpen ? 'true' : 'false'}
                              aria-controls=${this._domId(resortId, 'conditions')}
                              @click=${(e: Event) => this._toggleAccordion(resortId, 'conditions', e)}
                            >
                              <span>${localize(this.hass, 'component.bergfex-card.card.accordion.conditions')}</span>
                              <ha-icon
                                icon=${isConditionsOpen ? 'mdi:chevron-up' : 'mdi:chevron-down'}
                                aria-hidden="true"
                              ></ha-icon>
                            </button>
                          </h3>
                          ${
                            isConditionsOpen
                              ? html`
                                  <ul
                                    class="accordion-content details"
                                    id=${this._domId(resortId, 'conditions')}
                                    role="list"
                                  >
                                    ${
                                      snow_condition && !isCrossCountry
                                        ? this._renderConditionItem(
                                            snow_condition,
                                            html`<ha-icon icon="mdi:weather-snowy" aria-hidden="true"></ha-icon>`,
                                            'snow_condition',
                                          )
                                        : ''
                                    }
                                    ${
                                      slope_condition && !isCrossCountry
                                        ? this._renderConditionItem(
                                            slope_condition,
                                            html`<ha-icon icon="mdi:ski" aria-hidden="true"></ha-icon>`,
                                            'slope_condition',
                                          )
                                        : ''
                                    }
                                    ${
                                      avalanche_warning && !isCrossCountry
                                        ? this._renderConditionItem(
                                            avalanche_warning,
                                            html`<ha-icon icon="mdi:alert" aria-hidden="true"></ha-icon>`,
                                            'avalanche_warning',
                                          )
                                        : ''
                                    }
                                    ${
                                      classical_condition
                                        ? this._renderConditionItem(
                                            classical_condition,
                                            html`<span class="custom-icon fill" aria-hidden="true"
                                              >${unsafeSVG(classicCrossCountryIcon)}</span
                                            >`,
                                            'classical_condition',
                                          )
                                        : ''
                                    }
                                    ${
                                      skating_condition
                                        ? this._renderConditionItem(
                                            skating_condition,
                                            html`<span class="custom-icon fill" aria-hidden="true"
                                              >${unsafeSVG(skatingCrossCountryIcon)}</span
                                            >`,
                                            'skating_condition',
                                          )
                                        : ''
                                    }
                                    ${
                                      last_snowfall
                                        ? this._renderConditionItem(
                                            last_snowfall,
                                            html`<ha-icon icon="mdi:calendar-clock" aria-hidden="true"></ha-icon>`,
                                            'last_snowfall',
                                          )
                                        : ''
                                    }
                                    ${
                                      operation_status
                                        ? this._renderConditionItem(
                                            operation_status,
                                            html`<ha-icon icon="mdi:information-outline" aria-hidden="true"></ha-icon>`,
                                            'operation_status',
                                          )
                                        : ''
                                    }
                                  </ul>
                                `
                              : ''
                          }
                        </div>
                      `
                    : ''
                }
                ${(() => {
                  // Only show forecast if enabled and we have valid images
                  if (!this._config.show_forecast) return '';

                  const hasDailyImages =
                    resort.forecast_days &&
                    resort.forecast_days.length > 0 &&
                    resort.forecast_days.some((id) => {
                      const entity = this.hass.states[id];
                      return entity && entity.attributes.entity_picture;
                    });

                  const hasSummaryImages =
                    resort.forecast_summaries &&
                    resort.forecast_summaries.length > 0 &&
                    resort.forecast_summaries.some((id) => {
                      const entity = this.hass.states[id];
                      return entity && entity.attributes.entity_picture;
                    });

                  if (!hasDailyImages && !hasSummaryImages) return '';

                  const tabs: ForecastTab[] = [];
                  if (hasDailyImages) tabs.push('daily');
                  if (hasSummaryImages) tabs.push('summary');
                  const activeTab: ForecastTab = this._forecastState[resortId]?.tab || 'daily';
                  const panelId = this._domId(resortId, 'forecast-panel');
                  const forecastTitle = localize(this.hass, 'component.bergfex-card.card.accordion.forecast');

                  return html`
                    <div class="accordion-container">
                      <h3 class="accordion-title">
                        <button
                          type="button"
                          class="accordion-header"
                          aria-expanded=${isForecastOpen ? 'true' : 'false'}
                          aria-controls=${this._domId(resortId, 'forecast')}
                          @click=${(e: Event) => this._toggleAccordion(resortId, 'forecast', e)}
                        >
                          <span>${forecastTitle}</span>
                          <ha-icon
                            icon=${isForecastOpen ? 'mdi:chevron-up' : 'mdi:chevron-down'}
                            aria-hidden="true"
                          ></ha-icon>
                        </button>
                      </h3>
                      ${
                        isForecastOpen
                          ? html`
                              <div class="forecast-container" id=${this._domId(resortId, 'forecast')}>
                                <div class="forecast-tabs" role="tablist" aria-label=${forecastTitle}>
                                  ${tabs.map((tab, i) => {
                                    const selected = tab === activeTab;
                                    // Roving focus: only the selected tab is in the tab
                                    // order, the arrow keys move between them. Should the
                                    // selected one not be on offer, the first stands in.
                                    const focusable = selected || (!tabs.includes(activeTab) && i === 0);
                                    return html`
                                      <button
                                        type="button"
                                        role="tab"
                                        id=${this._domId(resortId, `tab-${tab}`)}
                                        class=${classMap({ 'forecast-tab': true, active: selected })}
                                        aria-selected=${selected ? 'true' : 'false'}
                                        aria-controls=${panelId}
                                        tabindex=${focusable ? '0' : '-1'}
                                        @click=${(e: Event) => this._handleTabChange(resortId, tab, e)}
                                        @keydown=${(e: KeyboardEvent) => this._handleTabKeydown(resortId, tabs, tab, e)}
                                      >
                                        ${localize(this.hass, `component.bergfex-card.card.forecast.${tab}`)}
                                      </button>
                                    `;
                                  })}
                                </div>

                                <div
                                  class="forecast-carousel"
                                  id=${panelId}
                                  role="tabpanel"
                                  aria-labelledby=${tabs.includes(activeTab) ? this._domId(resortId, `tab-${activeTab}`) : nothing}
                                >
                                  ${(() => {
                                    const images =
                                      activeTab === 'daily' ? resort.forecast_days : resort.forecast_summaries;
                                    const currentIndex = this._forecastState[resortId]?.index || 0;

                                    if (!images || images.length === 0) return html``;

                                    const currentImageEntityId = images[currentIndex];
                                    const currentImageEntity = this.hass.states[currentImageEntityId];
                                    const imageUrl = currentImageEntity?.attributes.entity_picture;

                                    // Extract label based on entity ID or index
                                    let label: string;
                                    if (activeTab === 'daily') {
                                      const dayMatch = currentImageEntityId.match(/day_(\d+)/);
                                      const dayOffset = dayMatch ? parseInt(dayMatch[1], 10) : currentIndex;
                                      label = this._formatForecastDate(dayOffset);
                                    } else {
                                      const hourMatch = currentImageEntityId.match(/summary_image_(\d+)h/);
                                      const hours = hourMatch ? hourMatch[1] : '';
                                      label = localize(this.hass, 'component.bergfex-card.card.forecast.hour', {
                                        hours,
                                      });
                                    }

                                    // The label is the one live region in the card, and a
                                    // polite one: it changes only when the reader presses
                                    // previous or next, and they should hear where they landed.
                                    return html`
                                      <div class="forecast-image-container">
                                        ${
                                          imageUrl
                                            ? html`<button
                                                type="button"
                                                class="forecast-image-button"
                                                @click=${(e: Event) => {
                                                  e.stopPropagation();
                                                  this._handleMoreInfo(currentImageEntityId);
                                                }}
                                              >
                                                <img
                                                  src="${imageUrl}"
                                                  class="forecast-image"
                                                  alt=${localize(
                                                    this.hass,
                                                    'component.bergfex-card.card.forecast.image_alt',
                                                    { label },
                                                  )}
                                                />
                                              </button>`
                                            : html`<span
                                                >${localize(
                                                  this.hass,
                                                  'component.bergfex-card.card.forecast.image_unavailable',
                                                )}</span
                                              >`
                                        }
                                      </div>
                                      <div class="carousel-controls">
                                        <button
                                          type="button"
                                          class="carousel-btn"
                                          aria-label=${localize(this.hass, 'component.bergfex-card.card.forecast.previous')}
                                          @click=${(e: Event) =>
                                            this._handleCarouselChange(resortId, 'prev', images.length, e)}
                                          ?disabled=${images.length <= 1}
                                        >
                                          <ha-icon icon="mdi:chevron-left" aria-hidden="true"></ha-icon>
                                        </button>
                                        <span class="carousel-label" aria-live="polite">${label}</span>
                                        <button
                                          type="button"
                                          class="carousel-btn"
                                          aria-label=${localize(this.hass, 'component.bergfex-card.card.forecast.next')}
                                          @click=${(e: Event) =>
                                            this._handleCarouselChange(resortId, 'next', images.length, e)}
                                          ?disabled=${images.length <= 1}
                                        >
                                          <ha-icon icon="mdi:chevron-right" aria-hidden="true"></ha-icon>
                                        </button>
                                      </div>
                                    `;
                                  })()}
                                </div>
                              </div>
                            `
                          : ''
                      }
                    </div>
                  `;
                })()}

                <div class="resort-footer">
                  ${
                    this._config.show_link && link
                      ? html`
                          <a
                            href=${link}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="link-icon"
                            title=${linkTitle}
                            aria-label=${linkTitle}
                            @click=${(e: Event) => e.stopPropagation()}
                          >
                            <ha-icon icon="mdi:link-variant" aria-hidden="true"></ha-icon>
                          </a>
                        `
                      : html`<div></div>`
                  }
                  ${
                    this._config.show_last_updated && last_update && last_update_at
                      ? (() => {
                          const relative = formatRelativeTime(last_update_at, this.hass);
                          return html`
                            <button
                              type="button"
                              class="last-updated"
                              aria-label=${localize(this.hass, 'component.bergfex-card.card.a11y.last_updated', {
                                time: relative,
                              })}
                              @click=${(e: Event) => {
                                e.stopPropagation();
                                this._handleMoreInfo(last_update.entity_id);
                              }}
                            >
                              <ha-icon icon="mdi:clock-outline" aria-hidden="true"></ha-icon>
                              <time datetime=${last_update_at.toISOString()}>${relative}</time>
                            </button>
                          `;
                        })()
                      : ''
                  }
                </div>
              </article>
            `;
          })}
        </div>
      </ha-card>
    `;
  }

  static styles = css`
    ${unsafeCSS(styles)}
  `;
}

// A leftover copy of the standalone lovelace-bergfex-card may already have claimed this
// element name. customElements.define() throws on a duplicate, which would take down
// whichever bundle loads second - card and editor alike. Skip registration and tell the
// user how to resolve it instead.
if (customElements.get(ELEMENT_NAME)) {
  console.warn(
    `${ELEMENT_NAME}: another copy of this card is already loaded, so this one stays inactive. ` +
      'The card now ships with the Bergfex integration - uninstall "Bergfex Card" from HACS and reload your browser.',
  );
} else {
  customElements.define(ELEMENT_NAME, BergfexCard);
}

if (typeof window !== 'undefined') {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === ELEMENT_NAME)) {
    window.customCards.push({
      type: ELEMENT_NAME,
      name: 'Bergfex Card',
      description: 'A Lovelace card to display ski resort conditions from Bergfex.',
      documentationURL: 'https://github.com/timmaurice/bergfex',
      preview: true,
      getEntitySuggestion: (hass: HomeAssistant, entityId: string) => {
        const entity = hass.entities[entityId];
        if (entity?.platform === 'bergfex' && entity.device_id) {
          return {
            config: {
              type: `custom:${ELEMENT_NAME}`,
              resorts: [entity.device_id],
            },
          };
        }
        return null;
      },
    });
  }
}
