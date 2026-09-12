import { test, expect } from './fixtures/hass';
import { useDashboard } from './helpers/homeassistant';

/**
 * The card picker builds its preview from `getStubConfig()`. `setConfig()` used
 * to reject the empty resort list that returned, so picking the card left the
 * dialog showing an error card instead of a preview; the stub now also picks the
 * first resort the instance has, so the preview shows a real card. Only a
 * browser walking the real dialog sees either - the unit tests call `setConfig`
 * with a config that already has a resort in it.
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

    // Everything here is located structurally rather than by label. The suite
    // reuses the repository's own playground instance, whose interface language
    // is whatever the developer set it to - it is German at the time of writing,
    // and English labels matched nothing. The add button is the only ha-button
    // the view itself owns.
    const addCard = page.locator('hui-masonry-view > ha-button');
    await expect(addCard).toBeVisible({ timeout: 60_000 });
    await addCard.click();

    // The dialog opens on "by entity"; the card list lives behind the second
    // tab. Scoped to the dialog, because the dashboard's own view tabs are
    // ha-tab-group-tab too.
    const createDialog = page.locator('hui-dialog-create-card');
    await createDialog.locator('ha-tab-group-tab').nth(1).click();
    await createDialog.locator('ha-input-search input').first().fill('bergfex');

    // The card's name comes from its own customCards registration, so it is the
    // one string here that is not translated.
    const tile = page.locator('hui-card-picker .card').filter({ hasText: 'Bergfex Card' }).first();
    await expect(tile).toBeVisible({ timeout: 30_000 });
    await tile.click();

    // Picking the card configures it from getStubConfig() and previews it.
    const dialog = page.locator('hui-dialog-edit-card');
    const preview = dialog.locator('bergfex-card');
    await expect(preview.locator('ha-card')).toBeVisible({ timeout: 60_000 });

    // A rejected setConfig() shows up as an error card, never as our own card.
    await expect(dialog.locator('hui-error-card')).toHaveCount(0);

    // getStubConfig() picks the first resort the instance has, so the preview
    // shows a real card rather than the "pick a resort" placeholder - and no
    // warning row, which is what an unresolvable resort would produce.
    await expect(preview.locator('.resort').first()).toBeVisible({ timeout: 30_000 });
    await expect(preview.locator('.warning')).toHaveCount(0);

    // The editor is part of the same dialog, and it must come up too.
    await expect(dialog.locator('bergfex-card-editor ha-card')).toBeVisible({ timeout: 30_000 });

    expect(consoleErrors.filter((text) => /resort|setConfig|already been used/i.test(text))).toEqual([]);
  });
});
