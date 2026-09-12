import { beforeEach, describe, expect, it, vi } from 'vitest';
import '../src/editor';
import { BergfexCardEditor } from '../src/editor';
import { BergfexCardConfig, DEFAULT_CONFIG, HomeAssistant } from '../src/types';

interface HaForm extends HTMLElement {
  data?: BergfexCardConfig;
  computeHelper?: (schema: { name: string }) => string | undefined;
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

  describe('defaults', () => {
    it('shows every option in the state the card actually renders', async () => {
      // The two used to keep separate default lists, so the editor displayed
      // toggles as off for options the card was rendering.
      await setConfig({ resorts: ['device-a'] });
      const data = formData() as unknown as Record<string, unknown>;

      for (const [option, value] of Object.entries(DEFAULT_CONFIG)) {
        expect({ option, value: data[option] }).toEqual({ option, value });
      }
    });

    it('lets an explicit config override a default', async () => {
      await setConfig({ resorts: ['device-a'], show_trails: false, show_link: false });
      const data = formData() as unknown as Record<string, unknown>;

      expect(data.show_trails).toBe(false);
      expect(data.show_link).toBe(false);
      expect(data.show_snow).toBe(true);
    });
  });

  describe('field help', () => {
    const helper = (name: string) => {
      const form = editor.shadowRoot?.querySelector('ha-form') as HaForm | null;
      return form?.computeHelper?.({ name });
    };

    it('explains that summer-operation resorts are not hidden', async () => {
      await setConfig({ resorts: ['device-a'] });
      const text = helper('hide_closed_resorts');
      expect(text).toBeDefined();
      expect(text).toMatch(/summer/i);
    });

    it('leaves fields without a helper translation blank', async () => {
      await setConfig({ resorts: ['device-a'] });
      for (const name of ['title', 'resorts', 'show_snow', 'sort_by']) {
        expect(helper(name)).toBeUndefined();
      }
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

  describe('not baking the defaults into what it saves', () => {
    it('saves only what the user changed', async () => {
      // The editor used to write its whole working copy back, so toggling one
      // switch saved eleven settings the user never touched - and froze today's
      // defaults into that card, where a later change to a default could never
      // reach it.
      await setConfig({ type: 'custom:bergfex-card', resorts: ['device-a'] } as BergfexCardConfig);

      const config = await emit({ show_snow: false } as Partial<BergfexCardConfig>);

      expect(config).toEqual({ type: 'custom:bergfex-card', resorts: ['device-a'], show_snow: false });
    });

    it('drops a setting again once it is put back to its default', async () => {
      await setConfig({
        type: 'custom:bergfex-card',
        resorts: ['device-a'],
        show_snow: false,
      } as BergfexCardConfig);

      const config = await emit({ show_snow: true } as Partial<BergfexCardConfig>);

      expect('show_snow' in config).toBe(false);
    });

    it('drops an emptied title rather than saving an empty string', async () => {
      await setConfig({ type: 'custom:bergfex-card', resorts: ['device-a'], title: 'Snow' } as BergfexCardConfig);

      const config = await emit({ title: '' } as Partial<BergfexCardConfig>);

      expect('title' in config).toBe(false);
    });

    it('still shows the defaults on the form', async () => {
      // Stripping them from what is saved must not turn the toggles off.
      await setConfig({ type: 'custom:bergfex-card', resorts: ['device-a'] } as BergfexCardConfig);
      const data = formData() as unknown as Record<string, unknown>;

      for (const [option, value] of Object.entries(DEFAULT_CONFIG)) {
        expect({ option, value: data[option] }).toEqual({ option, value });
      }
    });
  });

  describe('the add button', () => {
    it('does not write an empty resort while the new slot is still blank', async () => {
      await setConfig({ type: 'custom:bergfex-card', resorts: ['device-a'] } as BergfexCardConfig);

      const config = await emit({
        resorts: ['device-a', ''],
      } as unknown as Partial<BergfexCardConfig>);

      expect(config.resorts).toEqual(['device-a']);
    });

    it('drops a blank object entry too', async () => {
      await setConfig({ type: 'custom:bergfex-card', resorts: ['device-a'] } as BergfexCardConfig);

      const config = await emit({
        resorts: ['device-a', { device: '' }],
      } as unknown as Partial<BergfexCardConfig>);

      expect(config.resorts).toEqual(['device-a']);
    });
  });
});
