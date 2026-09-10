import { test, expect } from './fixtures/hass';
import { deviceName, findResortDevice, reloadConfigEntry, setState, useDashboard } from './helpers/homeassistant';

/**
 * The card resolves a resort through the entity registry, so it can only be fed
 * entities the registry knows. The suite therefore takes a resort the running
 * instance already has and writes the states it wants onto it - the attribute
 * names below are the ones `sensor.py`'s `extra_state_attributes` really emits
 * (`link`, `elevation`, `total`), not invented ones.
 */
const SNOW_MOUNTAIN = '180';
const SNOW_VALLEY = '65';
const LIFTS_OPEN = '12';

let urlPath: string;
let resortName: string;
let configEntryId: string | null;

test.beforeAll(async () => {
  const resort = await findResortDevice();
  configEntryId = resort.configEntryId;
  resortName = await deviceName(resort.deviceId);

  const sensor = (suffix: string) => `sensor.${resort.slug}_${suffix}`;

  await setState(sensor('status'), 'open', {
    friendly_name: `${resortName} Status`,
    link: 'https://www.bergfex.at/e2e/',
  });
  await setState(sensor('snow_mountain'), SNOW_MOUNTAIN, {
    friendly_name: `${resortName} Snow Mountain`,
    unit_of_measurement: 'cm',
    elevation: 2400,
  });
  await setState(sensor('snow_valley'), SNOW_VALLEY, {
    friendly_name: `${resortName} Snow Valley`,
    unit_of_measurement: 'cm',
    elevation: 1200,
  });
  await setState(sensor('new_snow'), '0', {
    friendly_name: `${resortName} New Snow`,
    unit_of_measurement: 'cm',
  });
  await setState(sensor('lifts_open_count'), LIFTS_OPEN, {
    friendly_name: `${resortName} Lifts Open`,
    total: 30,
  });

  urlPath = await useDashboard('card', {
    views: [
      {
        title: 'Resorts',
        cards: [{ type: 'custom:bergfex-card', title: 'E2E resorts', resorts: [resort.deviceId] }],
      },
      { title: 'Elsewhere', cards: [{ type: 'markdown', content: 'nothing here' }] },
    ],
  });
});

test.afterAll(async () => {
  // Give the resort back to the coordinator, so the manual playground is
  // exactly as it was found.
  if (configEntryId) await reloadConfigEntry(configEntryId);
});

test.describe('The card on a real dashboard', () => {
  test('renders the resort the integration reports', async ({ page, consoleErrors }) => {
    await page.goto(`/${urlPath}/0`);

    // Assert on what the card paints, not on the custom element itself: the
    // host has no box of its own, so Playwright rightly calls it hidden.
    const card = page.locator('bergfex-card');
    await expect(card.locator('ha-card')).toBeVisible({ timeout: 60_000 });
    await expect(card.locator('.resort-name')).toHaveText(resortName);
    await expect(card.locator('.resort-status')).toBeVisible();
    await expect(card.locator('.details')).toContainText(`${SNOW_MOUNTAIN} cm`);
    await expect(card.locator('.details')).toContainText(`${SNOW_VALLEY} cm`);
    expect(consoleErrors).toEqual([]);
  });

  test('comes back after leaving the view and returning', async ({ page }) => {
    // Views are torn out of the DOM on a switch. A card that does not notice it
    // is visible again comes back empty, and no unit test sees that.
    await page.goto(`/${urlPath}/0`);
    const name = page.locator('bergfex-card').locator('.resort-name');
    await expect(name).toHaveText(resortName, { timeout: 60_000 });

    await page.getByRole('tab', { name: 'Elsewhere' }).click();
    await expect(page.locator('bergfex-card')).toHaveCount(0);

    await page.getByRole('tab', { name: 'Resorts' }).click();
    await expect(name).toHaveText(resortName, { timeout: 30_000 });
  });
});
