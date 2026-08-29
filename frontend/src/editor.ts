import { LitElement, html, css, TemplateResult, unsafeCSS } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant, LovelaceCardEditor, BergfexCardConfig } from './types';
import { localize } from './localize';
import { fireEvent } from './utils';
import editorStyles from './styles/editor.styles.scss';

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
    title: 'groups.ski_only',
    schema: [
      { name: 'show_snow', selector: { boolean: {} } },
      { name: 'show_lifts_slopes', selector: { boolean: {} } },
      { name: 'show_forecast', selector: { boolean: {} } },
      { name: 'forecast_default_open', selector: { boolean: {} } },
    ],
  },
];

@customElement('bergfex-card-editor')
export class BergfexCardEditor extends LitElement implements LovelaceCardEditor {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private _config!: BergfexCardConfig;

  public setConfig(config: BergfexCardConfig): void {
    this._config = {
      show_snow: true,
      show_lifts_slopes: true,
      show_conditions: true,
      show_forecast: false,
      show_trend: false,
      conditions_default_open: false,
      forecast_default_open: false,
      ...config,
    };
  }

  private _valueChanged(ev: { detail: { value: Partial<BergfexCardConfig> } }): void {
    if (!this.hass || !this._config) return;

    fireEvent(this, 'config-changed', { config: { ...this._config, ...ev.detail.value } });
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

    return html`
      <ha-card>
        <div class="card-content card-config">
          <ha-form
            .schema=${schema}
            .hass=${this.hass}
            .data=${this._config}
            .computeLabel=${(s: { name: string }) => localize(this.hass, `component.bergfex-card.editor.${s.name}`)}
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
