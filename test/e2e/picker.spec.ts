import { test, expect } from './fixtures/hass';
import { useDashboard } from './helpers/homeassistant';

/**
 * The card picker builds its preview from `getStubConfig()`, which returns an
 * empty resort list. `setConfig()` used to reject that, so picking the card left
 * the dialog showing an error card instead of a preview. Only a browser walking
 * the real dialog sees this - the unit tests call `setConfig` with a config that
 * already has a resort in it.
 */
let urlPath: string;

test.beforeAll(async () => {
  urlPath = await useDashboard('picker', {
    views: [{ title: 'Picker', cards: [{ type: 'markdown', content: 'placeholder' }] }],
  });
});

test.describe('The card picker', () => {
  test('previews the card from its stub config without an error', async ({ page, consoleErrors }) => {
    await page.goto(`/${urlPath}/0?edit=1`);

    const addCard = page.getByRole('button', { name: /add card/i });
    await expect(addCard).toBeVisible({ timeout: 60_000 });
    await addCard.click();

    // The dialog opens on "by entity"; the card list lives behind the second tab.
    await page.locator('ha-tab-group-tab').filter({ hasText: 'By card' }).click();
    const search = page.locator('hui-card-picker ha-input-search input').first();
    await search.fill('bergfex');

    const tile = page.locator('hui-card-picker .card').filter({ hasText: 'Bergfex Card' }).first();
    await expect(tile).toBeVisible({ timeout: 30_000 });
    await tile.click();

    // Picking the card configures it from getStubConfig() and previews it.
    const dialog = page.locator('hui-dialog-edit-card');
    const preview = dialog.locator('bergfex-card');
    await expect(preview.locator('ha-card')).toBeVisible({ timeout: 60_000 });

    // A rejected setConfig() shows up as an error card, never as our own card.
    await expect(dialog.locator('hui-error-card')).toHaveCount(0);

    // The empty stub is a legitimate state: the card asks for a resort rather
    // than throwing.
    await expect(preview.locator('ha-card')).toContainText(/resort/i);

    // The editor is part of the same dialog, and it must come up too.
    await expect(dialog.locator('bergfex-card-editor ha-card')).toBeVisible({ timeout: 30_000 });

    expect(consoleErrors.filter((text) => /resort|setConfig|already been used/i.test(text))).toEqual([]);
  });
});
