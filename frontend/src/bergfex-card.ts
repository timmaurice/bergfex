import { LitElement, TemplateResult, html, css, unsafeCSS } from 'lit';
import { property, state, query } from 'lit/decorators.js';
import {
  HomeAssistant,
  LovelaceCard,
  LovelaceCardEditor,
  ResortConfig,
  BergfexCardConfig,
  DEFAULT_CONFIG,
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
  // The wording is taken from the integration's own KEYWORDS map in
  // const.py, which is what bergfex actually prints on each language's pages.
  // Seven languages were listed here and eleven were not, so a resort set up
  // in Hungarian showed "nincs jelentés" as if it were a snow condition.
  //
  // Those entries then turned out to be wrong for fourteen of the eighteen: the
  // phrases below marked (live) were read off bergfex on 2026-09-12 by taking the
  // German page of the same resort and field as the reference. The older
  // spellings are kept - bergfex is not consistent between its own pages, and
  // the integration normalises what it recognises to `unknown` anyway, so this
  // list only has to catch what reaches the card unnormalised.
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
  @state() private _forecastState: Record<string, { tab: 'daily' | 'summary'; index: number }> = {};
  @state() private _accordionState: Record<string, Record<string, boolean>> = {};
  @state() private _historyState: Record<string, string> = {}; // entity_id -> state 24h ago

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

    if (this._config.show_trend) {
      this._fetchHistory();
    }
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
   * Home Assistant calls this before the element has a hass of its own, and on
   * an instance that may have no bergfex resort at all, so nothing in here may
   * throw - a stub that throws leaves the picker showing an error tile.
   *
   * It returns `resorts` and nothing else on purpose. Every other setting has a
   * default in DEFAULT_CONFIG, and writing those into the saved config would
   * freeze today's defaults into every card anyone ever adds.
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
   * A fixed 3 made a card with six resorts claim the height of a card with one,
   * so masonry packed the column wrongly and the layout jumped once the real
   * card rendered.
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
   * Without this a section gives every custom card the same default box, so a
   * six-resort card was cropped and a one-resort card floated in whitespace.
   */
  public getGridOptions(): Record<string, number> {
    return {
      columns: 12,
      min_columns: 6,
      rows: this.getCardSize(),
      min_rows: 2,
    };
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
      const showTrendChanged = this.getOldConfig(changedProperties)?.show_trend !== this._config.show_trend;

      if (showTrendChanged && this._config.show_trend) {
        this._fetchHistory();
      }

      // The language is not the only thing the card reads off `hass`: the
      // forecast date and the season teaser format against `locale.language`,
      // and every number goes through `locale.number_format`. Watching only
      // `language` meant a profile change that touched just the locale left the
      // card showing the previous format until something else happened to
      // re-render it.
      const localeChanged =
        oldHass.language !== this.hass.language ||
        oldHass.locale?.language !== this.hass.locale?.language ||
        oldHass.locale?.number_format !== this.hass.locale?.number_format ||
        oldHass.locale?.time_format !== this.hass.locale?.time_format;

      return hasChanged || localeChanged || changedProperties.has('_historyState');
    }

    return true; // First render
  }

  private getOldConfig(changedProperties: Map<string | number | symbol, unknown>): BergfexCardConfig | undefined {
    return changedProperties.get('_config') as BergfexCardConfig | undefined;
  }

  private async _fetchHistory(): Promise<void> {
    if (!this.hass || !this._config.resorts) return;

    const resorts = this._getResorts(this.hass, this._config);
    const snowEntities = Object.values(resorts)
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

    if (snowEntities.length === 0) return;

    this._historyState = await fetchHistory(this.hass, snowEntities, 24);
  }

  private _renderTrend(entityId: string, currentState: string): TemplateResult {
    if (!this._config.show_trend) return html``;
    const oldState = this._historyState[entityId];
    if (oldState === undefined || this._isNA(currentState) || this._isNA(oldState)) return html``;

    const currentVal = parseFloat(currentState);
    const oldVal = parseFloat(oldState);

    if (isNaN(currentVal) || isNaN(oldVal)) return html``;

    if (currentVal > oldVal) {
      return html`<ha-icon class="trend-icon up" icon="mdi:trending-up"></ha-icon>`;
    } else if (currentVal < oldVal) {
      return html`<ha-icon class="trend-icon down" icon="mdi:trending-down"></ha-icon>`;
    } else {
      return html`<ha-icon class="trend-icon same" icon="mdi:trending-neutral"></ha-icon>`;
    }
  }

  private _handleMoreInfo(entityId: string): void {
    fireEvent(this, 'hass-more-info', { entityId });
  }

  private _handleTabChange(resortId: string, tab: 'daily' | 'summary', e: Event): void {
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
   * The integration has changed its unique id scheme, and where an installation
   * carries entities from more than one of them the registry holds both. The
   * superseded rows have no entity behind them any more: Home Assistant keeps
   * them in `states` as `unavailable` with `restored` set, and they sat on the
   * same device as the live ones, so the carousel collected twice as many
   * images and every second slot rendered "Image not available".
   *
   * Matching on `restored` rather than on `unavailable` is deliberate - a
   * resort whose coordinator is failing is unavailable too, and that is worth
   * showing rather than hiding.
   *
   * The states are read off the `hass` passed in, not off `this.hass`: the
   * caller is also used to build the previous picture in shouldUpdate.
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
      // The day and month were assembled by hand as "02.12.", which is the
      // German order printed at every user regardless of their locale. Intl
      // knows the right order and separator for each one.
      //
      // The month is named for the same reason the season teaser names it: an
      // all-numeric "12/04" is the 12th of April or the 4th of December
      // depending on who reads it. A forecast date is only five days out, so
      // context narrows it - but there is no reason for the two dates in one
      // card to disagree on the format.
      const locale = this.hass.locale?.language || this.hass.language || 'en';
      return date.toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' });
    }
  }

  private _renderProgressBar(value: number, total: number): TemplateResult {
    const percentage = Math.min(100, Math.max(0, (value / total) * 100));
    return html`
      <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: ${percentage}%"></div>
      </div>
    `;
  }

  /**
   * Whether a state carries no report at all.
   *
   * bergfex writes "no report" in the language of the page the resort was set
   * up in, and Home Assistant has its own two words for it. Only the German one
   * was listed, so a resort configured in English, French or Italian printed
   * bergfex's own phrase - or "unavailable" - into the card as if it were a
   * snow condition.
   */
  private _isNA(state: string): boolean {
    return NO_REPORT_STATES.includes(state?.trim().toLowerCase());
  }

  /**
   * Condition sensors carry free text from bergfex, but fall back to Home
   * Assistant's own `unknown` when there is no report. That constant is not
   * translatable, so printing the state verbatim showed English inside an
   * otherwise localized card.
   */
  /**
   * Resolve the badge shown next to a resort name.
   *
   * "Open" stays the operational state - lifts running, within opening hours.
   * The remaining cases used to collapse into a single red "Closed", which in
   * summer sat above a column of N/A and explained nothing. Naming the running
   * period instead tells the user why there is no snow report.
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

    // "ab 12/04" is either the 12th of April or the 4th of December depending
    // on who is reading it, and a season start is exactly the value nobody can
    // guess from context. Naming the month is the fix; it cannot be read the
    // wrong way round.
    //
    // `hass.locale.language` is preferred over `hass.language` only for form's
    // sake - both are the same profile language, so it changes nothing today.
    // The setting that actually decides date format is `locale.date_format`,
    // which this card does not read at all.
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
   * "Sommerbetrieb" and it may well be running lifts. Filtering on the status
   * sensor alone hid every resort from April to November and left an empty card.
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

  protected render(): TemplateResult {
    if (!this._config) {
      return html``;
    }

    // The picker previews the card without hass and without a resort. Render the
    // empty card with the hint instead of nothing, so the preview tile shows
    // what the card is rather than a blank box.
    if (!this.hass || this._config.resorts.length === 0) {
      return html`
        <ha-card .header=${this._config.title} tabindex="0">
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
      <ha-card .header=${this._config.title} tabindex="0">
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

            return html`
              <div class="resort" tabindex="0" @click=${() => this._handleMoreInfo(primaryEntity)}>
                <div class="resort-header">
                  <span class="resort-name">${resortName}</span>
                  <div class="resort-status-group">
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

                <div class=${isCrossCountry ? 'details cross-country-details' : 'details'}>
                  ${
                    this._config.show_snow && !isCrossCountry
                      ? html`
                          <div
                            class=${classMap({
                              'detail-item': true,
                              'n-a': !snow_mountain || isNaN(parseFloat(snow_mountain.state)),
                            })}
                            @click=${(e: Event) => {
                              e.stopPropagation();
                              if (snow_mountain) {
                                this._handleMoreInfo(snow_mountain.entity_id);
                              }
                            }}
                          >
                            <span class="custom-icon stroke">${unsafeSVG(mountainIcon)}</span>
                            <div class="detail-item-value">
                              ${
                                snow_mountain && !isNaN(parseFloat(snow_mountain.state))
                                  ? html`<div class="value-row">
                                      <span
                                        >${formatNumber(snow_mountain.state, this.hass)}
                                        ${snow_mountain.attributes.unit_of_measurement ?? ''}</span
                                      >
                                      ${this._renderTrend(snow_mountain.entity_id, snow_mountain.state)}
                                    </div>`
                                  : html`<span>N/A</span>`
                              }
                              <span class="detail-item-label"
                                >${localize(this.hass, 'component.bergfex-card.card.header.snow_mountain')}
                                ${
                                  snow_mountain?.attributes.elevation ? `(${snow_mountain.attributes.elevation}m)` : ''
                                }</span
                              >
                            </div>
                          </div>
                          <div
                            class=${classMap({
                              'detail-item': true,
                              'n-a': !snow_valley || isNaN(parseFloat(snow_valley.state)),
                            })}
                            @click=${(e: Event) => {
                              e.stopPropagation();
                              if (snow_valley) {
                                this._handleMoreInfo(snow_valley.entity_id);
                              }
                              // Highlight the clicked element
                              const target = e.currentTarget as HTMLElement;
                              target.classList.add('clicked');
                              setTimeout(() => {
                                target.classList.remove('clicked');
                              }, 500);
                            }}
                          >
                            <span class="custom-icon stroke">${unsafeSVG(valleyIcon)}</span>
                            <div class="detail-item-value">
                              ${
                                snow_valley && !isNaN(parseFloat(snow_valley.state))
                                  ? html`<div class="value-row">
                                      <span
                                        >${formatNumber(snow_valley.state, this.hass)}
                                        ${snow_valley.attributes.unit_of_measurement ?? ''}</span
                                      >
                                      ${this._renderTrend(snow_valley.entity_id, snow_valley.state)}
                                    </div>`
                                  : html`<span>N/A</span>`
                              }
                              <span class="detail-item-label"
                                >${localize(this.hass, 'component.bergfex-card.card.header.snow_valley')}
                                ${snow_valley?.attributes.elevation ? `(${snow_valley.attributes.elevation}m)` : ''}</span
                              >
                            </div>
                          </div>
                          <div
                            class=${classMap({
                              'detail-item': true,
                              'n-a': !new_snow || isNaN(parseFloat(new_snow.state)),
                            })}
                            @click=${(e: Event) => {
                              e.stopPropagation();
                              if (new_snow) {
                                this._handleMoreInfo(new_snow.entity_id);
                              }
                            }}
                          >
                            <ha-icon icon="mdi:weather-snowy-heavy"></ha-icon>
                            <div class="detail-item-value">
                              ${
                                new_snow && !isNaN(parseFloat(new_snow.state))
                                  ? html`<div class="value-row">
                                      <span
                                        >${formatNumber(new_snow.state, this.hass)}
                                        ${new_snow.attributes.unit_of_measurement ?? ''}</span
                                      >
                                      ${this._renderTrend(new_snow.entity_id, new_snow.state)}
                                    </div>`
                                  : html`<span>N/A</span>`
                              }
                              <span class="detail-item-label"
                                >${localize(this.hass, 'component.bergfex-card.card.header.new_snow')}</span
                              >
                            </div>
                          </div>
                        `
                      : ''
                  }
                  ${
                    isCrossCountry && this._config.show_trails
                      ? html`
                          ${
                            classical_open_km
                              ? html`
                                  <div
                                    class=${classMap({
                                      'detail-item': true,
                                      'n-a': !classical_open_km || isNaN(parseFloat(classical_open_km.state)),
                                    })}
                                    @click=${(e: Event) => {
                                      e.stopPropagation();
                                      if (classical_open_km) {
                                        this._handleMoreInfo(classical_open_km.entity_id);
                                      }
                                    }}
                                  >
                                    <span class="custom-icon fill">${unsafeSVG(classicCrossCountryIcon)}</span>
                                    <div class="detail-item-value">
                                      ${
                                        classical_open_km && !isNaN(parseFloat(classical_open_km.state))
                                          ? (() => {
                                              const openVal = parseFloat(classical_open_km.state);
                                              const unit = classical_open_km.attributes.unit_of_measurement ?? 'km';
                                              const totalVal = classical_total
                                                ? parseFloat(String(classical_total))
                                                : NaN;
                                              if (!isNaN(totalVal)) {
                                                return html`<div class="value-row">
                                                    <span
                                                      >${formatNumber(openVal, this.hass)}/${formatNumber(totalVal, this.hass)}
                                                      ${unit}</span
                                                    >
                                                    ${this._renderTrend(classical_open_km.entity_id, classical_open_km.state)}
                                                  </div>
                                                  ${this._renderProgressBar(openVal, totalVal)}`;
                                              }
                                              return html`<div class="value-row">
                                                <span>${formatNumber(classical_open_km.state, this.hass)} ${unit}</span>
                                                ${this._renderTrend(classical_open_km.entity_id, classical_open_km.state)}
                                              </div>`;
                                            })()
                                          : html`<span>N/A</span>`
                                      }
                                      <span class="detail-item-label"
                                        >${localize(this.hass, 'component.bergfex-card.card.header.classical_trails')}</span
                                      >
                                    </div>
                                  </div>
                                `
                              : ''
                          }
                          ${
                            skating_open_km
                              ? html`
                                  <div
                                    class=${classMap({
                                      'detail-item': true,
                                      'n-a': !skating_open_km || isNaN(parseFloat(skating_open_km.state)),
                                    })}
                                    @click=${(e: Event) => {
                                      e.stopPropagation();
                                      if (skating_open_km) {
                                        this._handleMoreInfo(skating_open_km.entity_id);
                                      }
                                    }}
                                  >
                                    <span class="custom-icon fill">${unsafeSVG(skatingCrossCountryIcon)}</span>
                                    <div class="detail-item-value">
                                      ${
                                        skating_open_km && !isNaN(parseFloat(skating_open_km.state))
                                          ? (() => {
                                              const openVal = parseFloat(skating_open_km.state);
                                              const unit = skating_open_km.attributes.unit_of_measurement ?? 'km';
                                              const totalVal = skating_total ? parseFloat(String(skating_total)) : NaN;
                                              if (!isNaN(totalVal)) {
                                                return html`<div class="value-row">
                                                    <span
                                                      >${formatNumber(openVal, this.hass)}/${formatNumber(totalVal, this.hass)}
                                                      ${unit}</span
                                                    >
                                                    ${this._renderTrend(skating_open_km.entity_id, skating_open_km.state)}
                                                  </div>
                                                  ${this._renderProgressBar(openVal, totalVal)}`;
                                              }
                                              return html`<div class="value-row">
                                                <span>${formatNumber(skating_open_km.state, this.hass)} ${unit}</span>
                                                ${this._renderTrend(skating_open_km.entity_id, skating_open_km.state)}
                                              </div>`;
                                            })()
                                          : html`<span>N/A</span>`
                                      }
                                      <span class="detail-item-label"
                                        >${localize(this.hass, 'component.bergfex-card.card.header.skating_trails')}</span
                                      >
                                    </div>
                                  </div>
                                `
                              : ''
                          }
                        `
                      : html`
                          ${
                            this._config.show_lifts_slopes && lifts_open_entity
                              ? html`
                                  <div
                                    class=${classMap({
                                      'detail-item': true,
                                      'n-a': !lifts_open_entity || isNaN(parseFloat(lifts_open_entity.state)),
                                    })}
                                    @click=${(e: Event) => {
                                      e.stopPropagation();
                                      if (lifts_open_entity) {
                                        this._handleMoreInfo(lifts_open_entity.entity_id);
                                      }
                                    }}
                                  >
                                    <ha-icon icon="mdi:gondola"></ha-icon>
                                    <div class="detail-item-value">
                                      ${
                                        lifts_open_entity && !isNaN(parseFloat(lifts_open_entity.state))
                                          ? (() => {
                                              const openVal = parseFloat(lifts_open_entity.state);
                                              const totalRaw = lifts_total;
                                              const totalVal = totalRaw ? parseFloat(String(totalRaw)) : NaN;
                                              if (!isNaN(totalVal)) {
                                                return html`<div class="value-row">
                                                    <span
                                                      >${formatNumber(openVal, this.hass)}/${formatNumber(totalVal, this.hass)}</span
                                                    >
                                                    ${this._renderTrend(lifts_open_entity.entity_id, lifts_open_entity.state)}
                                                  </div>
                                                  ${this._renderProgressBar(openVal, totalVal)}`;
                                              }
                                              return html`<div class="value-row">
                                                <span>${formatNumber(lifts_open_entity.state, this.hass)}</span>
                                                ${this._renderTrend(lifts_open_entity.entity_id, lifts_open_entity.state)}
                                              </div>`;
                                            })()
                                          : html`<span>N/A</span>`
                                      }
                                      <span class="detail-item-label"
                                        >${localize(this.hass, 'component.bergfex-card.card.lifts_open')}</span
                                      >
                                    </div>
                                  </div>
                                `
                              : ''
                          }
                          ${
                            this._config.show_lifts_slopes && (slopes_open_km || slopes_open_entity)
                              ? html`
                                  ${
                                    slopes_open_km
                                      ? html`
                                          <div
                                            class=${classMap({
                                              'detail-item': true,
                                              'n-a': !slopes_open_km || isNaN(parseFloat(slopes_open_km.state)),
                                            })}
                                            @click=${(e: Event) => {
                                              e.stopPropagation();
                                              if (slopes_open_km) {
                                                this._handleMoreInfo(slopes_open_km.entity_id);
                                              }
                                            }}
                                          >
                                            <span class="custom-icon stroke">
                                              <ha-icon icon="mdi:slope-downhill"></ha-icon>
                                            </span>
                                            <div class="detail-item-value">
                                              ${
                                                slopes_open_km && !isNaN(parseFloat(slopes_open_km.state))
                                                  ? (() => {
                                                      const openVal = parseFloat(slopes_open_km.state);
                                                      const totalRaw = slopes_total_km;
                                                      const totalVal = totalRaw ? parseFloat(String(totalRaw)) : NaN;
                                                      const unit =
                                                        slopes_open_km.attributes.unit_of_measurement ?? 'km';
                                                      if (!isNaN(totalVal)) {
                                                        return html`<div class="value-row">
                                                            <span
                                                              >${formatNumber(openVal, this.hass)}/${formatNumber(totalVal, this.hass)}
                                                              ${unit}</span
                                                            >
                                                            ${this._renderTrend(slopes_open_km.entity_id, slopes_open_km.state)}
                                                          </div>
                                                          ${this._renderProgressBar(openVal, totalVal)}`;
                                                      }
                                                      return html`<div class="value-row">
                                                        <span
                                                          >${formatNumber(slopes_open_km.state, this.hass)}
                                                          ${unit}</span
                                                        >
                                                        ${this._renderTrend(slopes_open_km.entity_id, slopes_open_km.state)}
                                                      </div>`;
                                                    })()
                                                  : html`<span>N/A</span>`
                                              }
                                              <span class="detail-item-label"
                                                >${localize(
                                                  this.hass,
                                                  'component.bergfex-card.card.header.slopes_info_km',
                                                )}</span
                                              >
                                            </div>
                                          </div>
                                        `
                                      : ''
                                  }
                                  ${
                                    slopes_open_entity && slopes_total // With total
                                      ? html`
                                          <div
                                            class=${classMap({
                                              'detail-item': true,
                                              'n-a':
                                                !slopes_open_entity ||
                                                isNaN(parseFloat(slopes_open_entity.state)) ||
                                                isNaN(parseFloat(String(slopes_total ?? NaN))),
                                            })}
                                            @click=${(e: Event) => {
                                              e.stopPropagation();
                                              if (slopes_open_entity) {
                                                this._handleMoreInfo(slopes_open_entity.entity_id);
                                              }
                                            }}
                                          >
                                            <ha-icon icon="mdi:counter"></ha-icon>
                                            <div class="detail-item-value">
                                              ${
                                                slopes_open_entity && !isNaN(parseFloat(slopes_open_entity.state))
                                                  ? (() => {
                                                      const openVal = parseFloat(slopes_open_entity.state);
                                                      const totalRaw = slopes_total;
                                                      const totalVal = totalRaw ? parseFloat(String(totalRaw)) : NaN;
                                                      if (!isNaN(totalVal)) {
                                                        return html`<div class="value-row">
                                                            <span
                                                              >${formatNumber(openVal, this.hass)}/${formatNumber(totalVal, this.hass)}</span
                                                            >
                                                            ${this._renderTrend(
                                                              slopes_open_entity.entity_id,
                                                              slopes_open_entity.state,
                                                            )}
                                                          </div>
                                                          ${this._renderProgressBar(openVal, totalVal)}`;
                                                      }
                                                      return html`<div class="value-row">
                                                        <span
                                                          >${formatNumber(slopes_open_entity.state, this.hass)}</span
                                                        >
                                                        ${this._renderTrend(
                                                          slopes_open_entity.entity_id,
                                                          slopes_open_entity.state,
                                                        )}
                                                      </div>`;
                                                    })()
                                                  : html`<span>N/A</span>`
                                              }
                                              <span class="detail-item-label"
                                                >${localize(this.hass, 'component.bergfex-card.card.header.slopes_info')}
                                                (${localize(
                                                  this.hass,
                                                  'component.bergfex-card.card.header.slopes_total',
                                                )})</span
                                              >
                                            </div>
                                          </div>
                                        `
                                      : slopes_open_entity // Without total
                                        ? html`
                                            <div
                                              class=${classMap({
                                                'detail-item': true,
                                                'n-a':
                                                  !slopes_open_entity || isNaN(parseFloat(slopes_open_entity.state)),
                                              })}
                                              @click=${(e: Event) => {
                                                e.stopPropagation();
                                                if (slopes_open_entity) {
                                                  this._handleMoreInfo(slopes_open_entity.entity_id);
                                                }
                                              }}
                                            >
                                              <ha-icon icon="mdi:counter"></ha-icon>
                                              <div class="detail-item-value">
                                                ${
                                                  slopes_open_entity && !isNaN(parseFloat(slopes_open_entity.state))
                                                    ? html`<div class="value-row">
                                                        <span
                                                          >${formatNumber(slopes_open_entity.state, this.hass)}</span
                                                        >
                                                        ${this._renderTrend(
                                                          slopes_open_entity.entity_id,
                                                          slopes_open_entity.state,
                                                        )}
                                                      </div>`
                                                    : html`<span>N/A</span>`
                                                }
                                                <span class="detail-item-label"
                                                  >${localize(
                                                    this.hass,
                                                    'component.bergfex-card.card.header.slopes_info',
                                                  )}</span
                                                >
                                              </div>
                                            </div>
                                          `
                                        : ''
                                  }
                                `
                              : ''
                          }
                        `
                  }
                </div>

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
                          <div
                            class="accordion-header"
                            @click=${(e: Event) => this._toggleAccordion(resortId, 'conditions', e)}
                          >
                            <span>${localize(this.hass, 'component.bergfex-card.card.accordion.conditions')}</span>
                            <ha-icon icon=${isConditionsOpen ? 'mdi:chevron-up' : 'mdi:chevron-down'}></ha-icon>
                          </div>
                          ${
                            isConditionsOpen
                              ? html`
                                  <div class="accordion-content details">
                                    ${
                                      this._config.show_conditions &&
                                      (snow_condition || slope_condition) &&
                                      !isCrossCountry
                                        ? html`
                                            ${
                                              snow_condition
                                                ? html`
                                                    <div
                                                      class=${classMap({
                                                        'detail-item': true,
                                                        'n-a': this._isNA(snow_condition.state),
                                                      })}
                                                      @click=${(e: Event) => {
                                                        e.stopPropagation();
                                                        if (snow_condition) {
                                                          this._handleMoreInfo(snow_condition.entity_id);
                                                        }
                                                      }}
                                                    >
                                                      <ha-icon icon="mdi:weather-snowy"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(snow_condition.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${localize(
                                                            this.hass,
                                                            'component.bergfex-card.card.header.snow_condition',
                                                          )}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `
                                                : ''
                                            }
                                            ${
                                              slope_condition
                                                ? html`
                                                    <div
                                                      class=${classMap({
                                                        'detail-item': true,
                                                        'n-a': this._isNA(slope_condition.state),
                                                      })}
                                                      @click=${(e: Event) => {
                                                        e.stopPropagation();
                                                        if (slope_condition) {
                                                          this._handleMoreInfo(slope_condition.entity_id);
                                                        }
                                                      }}
                                                    >
                                                      <ha-icon icon="mdi:ski"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(slope_condition.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${localize(
                                                            this.hass,
                                                            'component.bergfex-card.card.header.slope_condition',
                                                          )}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `
                                                : ''
                                            }
                                          `
                                        : ''
                                    }
                                    ${
                                      this._config.show_conditions && avalanche_warning && !isCrossCountry
                                        ? html`
                                            <div
                                              class=${classMap({
                                                'detail-item': true,
                                                'n-a': this._isNA(avalanche_warning.state),
                                              })}
                                              @click=${(e: Event) => {
                                                e.stopPropagation();
                                                if (avalanche_warning) {
                                                  this._handleMoreInfo(avalanche_warning.entity_id);
                                                }
                                              }}
                                            >
                                              <ha-icon icon="mdi:alert"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(avalanche_warning.state)}</span>
                                                <span class="detail-item-label"
                                                  >${localize(
                                                    this.hass,
                                                    'component.bergfex-card.card.header.avalanche_warning',
                                                  )}</span
                                                >
                                              </div>
                                            </div>
                                          `
                                        : ''
                                    }
                                    ${
                                      this._config.show_conditions && (classical_condition || skating_condition)
                                        ? html`
                                            ${
                                              classical_condition
                                                ? html`
                                                    <div
                                                      class=${classMap({
                                                        'detail-item': true,
                                                        'n-a': this._isNA(classical_condition.state),
                                                      })}
                                                      @click=${(e: Event) => {
                                                        e.stopPropagation();
                                                        if (classical_condition) {
                                                          this._handleMoreInfo(classical_condition.entity_id);
                                                        }
                                                      }}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${unsafeSVG(classicCrossCountryIcon)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(classical_condition.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${localize(
                                                            this.hass,
                                                            'component.bergfex-card.card.header.classical_condition',
                                                          )}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `
                                                : ''
                                            }
                                            ${
                                              skating_condition
                                                ? html`
                                                    <div
                                                      class=${classMap({
                                                        'detail-item': true,
                                                        'n-a': this._isNA(skating_condition.state),
                                                      })}
                                                      @click=${(e: Event) => {
                                                        e.stopPropagation();
                                                        if (skating_condition) {
                                                          this._handleMoreInfo(skating_condition.entity_id);
                                                        }
                                                      }}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${unsafeSVG(skatingCrossCountryIcon)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(skating_condition.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${localize(
                                                            this.hass,
                                                            'component.bergfex-card.card.header.skating_condition',
                                                          )}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `
                                                : ''
                                            }
                                          `
                                        : ''
                                    }
                                    ${
                                      last_snowfall
                                        ? html`
                                            <div
                                              class=${classMap({
                                                'detail-item': true,
                                                'n-a': this._isNA(last_snowfall.state),
                                              })}
                                              @click=${(e: Event) => {
                                                e.stopPropagation();
                                                this._handleMoreInfo(last_snowfall.entity_id);
                                              }}
                                            >
                                              <ha-icon icon="mdi:calendar-clock"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(last_snowfall.state)}</span>
                                                <span class="detail-item-label"
                                                  >${localize(
                                                    this.hass,
                                                    'component.bergfex-card.card.header.last_snowfall',
                                                  )}</span
                                                >
                                              </div>
                                            </div>
                                          `
                                        : ''
                                    }
                                    ${
                                      this._config.show_conditions && operation_status
                                        ? html`
                                            <div
                                              class=${classMap({
                                                'detail-item': true,
                                                'n-a': this._isNA(operation_status.state),
                                              })}
                                              @click=${(e: Event) => {
                                                e.stopPropagation();
                                                if (operation_status) {
                                                  this._handleMoreInfo(operation_status.entity_id);
                                                }
                                              }}
                                            >
                                              <ha-icon icon="mdi:information-outline"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(operation_status.state)}</span>
                                                <span class="detail-item-label"
                                                  >${localize(
                                                    this.hass,
                                                    'component.bergfex-card.card.header.operation_status',
                                                  )}</span
                                                >
                                              </div>
                                            </div>
                                          `
                                        : ''
                                    }
                                  </div>
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

                  return html`
                    <div class="accordion-container">
                      <div
                        class="accordion-header"
                        @click=${(e: Event) => this._toggleAccordion(resortId, 'forecast', e)}
                      >
                        <span>${localize(this.hass, 'component.bergfex-card.card.accordion.forecast')}</span>
                        <ha-icon icon=${isForecastOpen ? 'mdi:chevron-up' : 'mdi:chevron-down'}></ha-icon>
                      </div>
                      ${
                        isForecastOpen
                          ? html`
                              <div class="forecast-container">
                                <div class="forecast-tabs">
                                  ${
                                    hasDailyImages
                                      ? html`
                                          <div
                                            class="forecast-tab ${
                                              !this._forecastState[resortId] ||
                                              this._forecastState[resortId].tab === 'daily'
                                                ? 'active'
                                                : ''
                                            }"
                                            @click=${(e: Event) => this._handleTabChange(resortId, 'daily', e)}
                                          >
                                            ${localize(this.hass, 'component.bergfex-card.card.forecast.daily')}
                                          </div>
                                        `
                                      : ''
                                  }
                                  ${
                                    hasSummaryImages
                                      ? html`
                                          <div
                                            class="forecast-tab ${
                                              this._forecastState[resortId]?.tab === 'summary' ? 'active' : ''
                                            }"
                                            @click=${(e: Event) => this._handleTabChange(resortId, 'summary', e)}
                                          >
                                            ${localize(this.hass, 'component.bergfex-card.card.forecast.summary')}
                                          </div>
                                        `
                                      : ''
                                  }
                                </div>

                                <div class="forecast-carousel">
                                  ${(() => {
                                    const activeTab = this._forecastState[resortId]?.tab || 'daily';
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

                                    return html`
                                      <div class="forecast-image-container">
                                        ${
                                          imageUrl
                                            ? html`<img
                                                src="${imageUrl}"
                                                class="forecast-image"
                                                alt="${label}"
                                                @click=${(e: Event) => {
                                                  e.stopPropagation();
                                                  this._handleMoreInfo(currentImageEntityId);
                                                }}
                                                style="cursor: pointer;"
                                              />`
                                            : html`<span>Image not available</span>`
                                        }
                                      </div>
                                      <div class="carousel-controls">
                                        <button
                                          class="carousel-btn"
                                          @click=${(e: Event) =>
                                            this._handleCarouselChange(resortId, 'prev', images.length, e)}
                                          ?disabled=${images.length <= 1}
                                        >
                                          <ha-icon icon="mdi:chevron-left"></ha-icon>
                                        </button>
                                        <span class="carousel-label">${label}</span>
                                        <button
                                          class="carousel-btn"
                                          @click=${(e: Event) =>
                                            this._handleCarouselChange(resortId, 'next', images.length, e)}
                                          ?disabled=${images.length <= 1}
                                        >
                                          <ha-icon icon="mdi:chevron-right"></ha-icon>
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
                            class="link-icon"
                            title=${localize(this.hass, 'component.bergfex-card.card.link_title', { resortName })}
                            @click=${(e: Event) => e.stopPropagation()}
                          >
                            <ha-icon icon="mdi:link-variant"></ha-icon>
                          </a>
                        `
                      : html`<div></div>`
                  }
                  ${
                    this._config.show_last_updated && last_update && last_update_at
                      ? html`
                          <div
                            class="last-updated"
                            @click=${(e: Event) => {
                              e.stopPropagation();
                              if (last_update) {
                                this._handleMoreInfo(last_update.entity_id);
                              }
                            }}
                          >
                            <ha-icon icon="mdi:clock-outline"></ha-icon>
                            <span>${formatRelativeTime(last_update_at, this.hass)}</span>
                          </div>
                        `
                      : ''
                  }
                </div>
              </div>
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
