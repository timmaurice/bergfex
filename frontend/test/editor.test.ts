import { beforeEach, describe, expect, it, vi } from 'vitest';
import '../src/editor';
import { BergfexCardEditor } from '../src/editor';
import { BergfexCardConfig, HomeAssistant } from '../src/types';

vi.mock('../src/localize.ts', () => ({
  localize: (_hass: unknown, key: string) => key,
}));

interface HaForm extends HTMLElement {
  data?: BergfexCardConfig;
}

describe('BergfexCardEditor', () => {
  let editor: BergfexCardEditor;
  let hass: HomeAssistant;

  beforeEach(async () => {
    hass = { language: 'en', states: {}, entities: {}, devices: {} } as unknown as HomeAssistant;
    editor = document.createElement('bergfex-card-editor') as BergfexCardEditor;
    document.body.appendChild(editor);
    editor.hass = hass;
  });

  const setConfig = async (config: Partial<BergfexCardConfig>) => {
    editor.setConfig(config as BergfexCardConfig);
    await editor.updateComplete;
  };

  const formData = () => (editor.shadowRoot?.querySelector('ha-form') as HaForm | null)?.data;

  /** ha-form emits the picker's value; capture what the editor forwards. */
  const emit = async (value: Partial<BergfexCardConfig>) => {
    const changed = vi.fn();
    editor.addEventListener('config-changed', (e) => changed((e as CustomEvent).detail.config));
    editor.shadowRoot?.querySelector('ha-form')?.dispatchEvent(new CustomEvent('value-changed', { detail: { value } }));
    await editor.updateComplete;
    return changed.mock.calls[0]?.[0] as BergfexCardConfig;
  };

  describe('reading the config', () => {
    it('passes plain device IDs straight through', async () => {
      await setConfig({ resorts: ['device-a', 'device-b'] });
      expect(formData()?.resorts).toEqual(['device-a', 'device-b']);
    });

    it('unwraps the { device, name } form instead of rendering [object Object]', async () => {
      await setConfig({
        resorts: [{ device: 'device-a', name: 'My Resort' }, { device: 'device-b' }],
      });
      expect(formData()?.resorts).toEqual(['device-a', 'device-b']);
    });

    it('skips null entries rather than passing them to the picker', async () => {
      await setConfig({
        resorts: [null, 'device-a', undefined] as unknown as BergfexCardConfig['resorts'],
      });
      expect(formData()?.resorts).toEqual(['device-a']);
    });
  });

  describe('writing the config', () => {
    it('keeps custom resort names when the picker returns bare IDs', async () => {
      await setConfig({
        resorts: [{ device: 'device-a', name: 'My Resort' }, { device: 'device-b' }],
      });

      const config = await emit({ resorts: ['device-a', 'device-b'] } as Partial<BergfexCardConfig>);

      expect(config.resorts).toEqual([{ device: 'device-a', name: 'My Resort' }, 'device-b']);
    });

    it('keeps custom names when an unrelated setting changes', async () => {
      await setConfig({
        resorts: [{ device: 'device-a', name: 'My Resort' }],
        show_snow: true,
      });

      const config = await emit({
        resorts: ['device-a'],
        show_snow: false,
      } as Partial<BergfexCardConfig>);

      expect(config.show_snow).toBe(false);
      expect(config.resorts).toEqual([{ device: 'device-a', name: 'My Resort' }]);
    });

    it('drops the name for a resort the user removed', async () => {
      await setConfig({
        resorts: [
          { device: 'device-a', name: 'My Resort' },
          { device: 'device-b', name: 'Other' },
        ],
      });

      const config = await emit({ resorts: ['device-b'] } as Partial<BergfexCardConfig>);

      expect(config.resorts).toEqual([{ device: 'device-b', name: 'Other' }]);
    });

    it('leaves a newly added resort as a bare ID', async () => {
      await setConfig({ resorts: [{ device: 'device-a', name: 'My Resort' }] });

      const config = await emit({ resorts: ['device-a', 'device-new'] } as Partial<BergfexCardConfig>);

      expect(config.resorts).toEqual([{ device: 'device-a', name: 'My Resort' }, 'device-new']);
    });
  });
});
