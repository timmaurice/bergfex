import { LitElement, html, css, TemplateResult, unsafeCSS } from 'lit';
import { property, state } from 'lit/decorators.js';
import {
  HomeAssistant,
  LovelaceCardEditor,
  BergfexCardConfig,
  ResortConfig,
  DEFAULT_CONFIG,
  withoutDefaults,
} from './types';
import { localize } from './localize';
import { fireEvent } from './utils';
import editorStyles from './styles/editor.styles.scss';

/**
 * The `resorts` config accepts either a bare device ID or a `{ device, name }`
 * object, the latter written by hand in YAML to override a resort's label.
 * ha-form's device selector only speaks device IDs.
 */
function toDeviceId(resort: ResortConfig): string {
  return typeof resort === 'string' ? resort : resort.device;
}

const SCHEMA = [
  { name: 'title', selector: { text: {} } },
  {
    name: 'resorts',
    selector: { device: { multiple: true, integration: 'bergfex' } },
  },
  {
    type: 'expandable',
    title: 'groups.display',
    schema: [
      { name: 'show_conditions', selector: { boolean: {} } },
      { name: 'conditions_default_open', selector: { boolean: {} } },
      { name: 'show_trend', selector: { boolean: {} } },
      { name: 'show_link', selector: { boolean: {} } },
      { name: 'show_last_updated', selector: { boolean: {} } },
      { name: 'hide_closed_resorts', selector: { boolean: {} } },
      { name: 'sort_by', selector: { select: { mode: 'dropdown' } } },
    ],
  },
  {
    type: 'expandable',
    title: 'groups.cross_country_only',
    schema: [{ name: 'show_trails', selector: { boolean: {} } }],
  },
  {
    type: 'expandable',
    title: 'groups.ski_only',
    schema: [
      { name: 'show_snow', selector: { boolean: {} } },
      { name: 'show_lifts_slopes', selector: { boolean: {} } },
      { name: 'show_forecast', selector: { boolean: {} } },
      { name: 'forecast_default_open', selector: { boolean: {} } },
    ],
  },
];

const EDITOR_ELEMENT_NAME = 'bergfex-card-editor';

export class BergfexCardEditor extends LitElement implements LovelaceCardEditor {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private _config!: BergfexCardConfig;

  public setConfig(config: BergfexCardConfig): void {
    // Kept as the user's own config, not merged with the defaults. Merging here
    // is what wrote every default back out again on the next edit; the defaults
    // are applied for display only, in render().
    this._config = config;
  }

  /**
   * Optional one-line explanation under a field.
   *
   * Only fields with an `<name>_helper` translation get one; localize echoes the
   * key back when it finds nothing, which is how absence is detected.
   */
  private _helper(name: string): string | undefined {
    const key = `component.bergfex-card.editor.${name}_helper`;
    const text = localize(this.hass, key);
    return text === key ? undefined : text;
  }

  private _valueChanged(ev: { detail: { value: Partial<BergfexCardConfig> } }): void {
    if (!this.hass || !this._config) return;

    const value = { ...ev.detail.value };

    if (Array.isArray(value.resorts)) {
      // The device picker hands back plain IDs. Without this, opening the editor
      // and changing any unrelated setting would silently drop every custom
      // resort name the user had written in YAML.
      const customNames = new Map<string, string>();
      for (const resort of this._config.resorts ?? []) {
        if (resort && typeof resort === 'object' && resort.name) {
          customNames.set(resort.device, resort.name);
        }
      }

      // "Add" hands back an empty slot until a device is picked in it. Emitting
      // that would write a blank resort into the config, which the card then has
      // to resolve and warn about.
      value.resorts = value.resorts
        .filter((resort) => Boolean(resort) && Boolean(toDeviceId(resort)))
        .map((resort) => {
          const device = toDeviceId(resort);
          const name = customNames.get(device);
          return name ? { device, name } : device;
        });
    }

    fireEvent(this, 'config-changed', { config: withoutDefaults({ ...this._config, ...value }) });
  }

  protected render(): TemplateResult {
    if (!this.hass || !this._config) {
      return html``;
    }
    // Helper to build options for sort_by with localized labels
    const sortOptions = [
      { value: 'mountain', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.mountain') },
      { value: 'valley', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.valley') },
      { value: 'new', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.new') },
      { value: 'lift', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.lift') },
      { value: 'classical', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.classical') },
      { value: 'skating', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.skating') },
      { value: 'update', label: localize(this.hass, 'component.bergfex-card.editor.sort_by_options.update') },
    ];

    // Compute schema and apply dynamic option transforms
    const computeSchema = (items: Record<string, unknown>[]): Record<string, unknown>[] => {
      return items.reduce(
        (acc, item) => {
          const newItem = { ...item } as Record<string, unknown>;

          // Handle expandable sections
          if (newItem.type === 'expandable' && Array.isArray(newItem.schema)) {
            const nested = (newItem.schema as Record<string, unknown>[]).map((n) => ({ ...n }));
            // Provide sort options if present
            if (newItem.title === 'groups.display') {
              nested.forEach((n) => {
                if (n.name === 'sort_by') {
                  n.selector = { select: { mode: 'dropdown', clearable: true, options: sortOptions } };
                }
              });
            }

            newItem.title =
              typeof newItem.title === 'string'
                ? localize(this.hass, `component.bergfex-card.editor.${newItem.title}`)
                : newItem.title;
            newItem.schema = nested;
            acc.push(newItem);
            return acc;
          }

          // For top-level resorts device selector, ensure integration is bergfex
          if (newItem.name === 'resorts') {
            newItem.selector = { device: { multiple: true, integration: 'bergfex' } };
          }

          acc.push(newItem);
          return acc;
        },
        [] as Record<string, unknown>[],
      );
    };

    const schema = computeSchema(SCHEMA);

    // Normalise resorts for the form; the object form renders as "[object Object]"
    // in the device picker and matches no device.
    // The defaults belong here and only here: the form has to show a toggle in
    // the position the card actually renders, without that position being
    // written back into the saved config.
    const formData = {
      ...DEFAULT_CONFIG,
      ...this._config,
      resorts: (this._config.resorts ?? []).filter(Boolean).map(toDeviceId),
    };

    return html`
      <ha-card>
        <div class="card-content card-config">
          <ha-form
            .schema=${schema}
            .hass=${this.hass}
            .data=${formData}
            .computeLabel=${(s: { name: string }) => localize(this.hass, `component.bergfex-card.editor.${s.name}`)}
            .computeHelper=${(s: { name: string }) => this._helper(s.name)}
            @value-changed=${this._valueChanged}
          ></ha-form>
        </div>
      </ha-card>
    `;
  }

  static styles = css`
    ${unsafeCSS(editorStyles)}
  `;
}

// Guarded for the same reason as the card itself: a stale standalone bundle may already
// have registered this element.
if (!customElements.get(EDITOR_ELEMENT_NAME)) {
  customElements.define(EDITOR_ELEMENT_NAME, BergfexCardEditor);
}
