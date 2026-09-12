"""Registry rows an older unique id scheme left behind.

The migration in __init__.py re-keys what it can and declines the rest: two rows
cannot share one unique id. What it declines stays on the device with nothing
behind it, which is what the duplicate forecast images turned out to be.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry, flush_store

from custom_components.bergfex.__init__ import (
    ORPHANED_ENTITIES_ISSUE_ID,
    _async_orphaned_registry_entries,
    _async_report_orphaned_entities,
)
from custom_components.bergfex.const import CONF_SKI_AREA, DOMAIN
from custom_components.bergfex.repairs import async_create_fix_flow
from custom_components.bergfex.unique_id import build_unique_id

AREA = "/tirol/achensee/"
CURRENT = build_unique_id(AREA, "snow_mountain")
# What sensor.py wrote when ids were keyed on the display name, and what
# image.py wrote at runtime with its own spelling of the same idea.
LEGACY_SENSOR = "bergfex_achensee_snow_valley"
LEGACY_IMAGE = "bergfex_achensee_/_forecast_image_24h"


def _entry(hass: HomeAssistant, name: str = "achensee") -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Achensee",
        data={CONF_SKI_AREA: AREA, "name": name},
        unique_id=AREA,
    )
    entry.add_to_hass(hass)
    return entry


def _register(hass, entry, unique_id, *, domain="sensor", object_id="x"):
    return er.async_get(hass).async_get_or_create(
        domain,
        DOMAIN,
        unique_id,
        config_entry=entry,
        suggested_object_id=object_id,
    )


class TestDetection:
    async def test_a_row_on_the_current_scheme_is_not_a_leftover(
        self, hass: HomeAssistant
    ):
        entry = _entry(hass)
        _register(hass, entry, CURRENT, object_id="current")

        assert _async_orphaned_registry_entries(hass, entry) == []

    async def test_a_row_from_a_superseded_scheme_is(self, hass: HomeAssistant):
        """Both older spellings count, since neither can be produced today."""
        entry = _entry(hass)
        _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")
        _register(hass, entry, LEGACY_IMAGE, domain="image", object_id="legacy_image")

        found = {row.unique_id for row in _async_orphaned_registry_entries(hass, entry)}
        assert found == {LEGACY_SENSOR, LEGACY_IMAGE}

    async def test_another_entry_s_rows_are_left_alone(self, hass: HomeAssistant):
        """The registry is shared; only this entry's rows are this entry's problem."""
        entry = _entry(hass)
        other = MockConfigEntry(
            domain=DOMAIN,
            title="Sölden",
            data={CONF_SKI_AREA: "/tirol/soelden/", "name": "Sölden"},
            unique_id="/tirol/soelden/",
        )
        other.add_to_hass(hass)
        _register(hass, other, "bergfex_soelden_snow_valley", object_id="soelden")

        assert _async_orphaned_registry_entries(hass, entry) == []


class TestTheIssue:
    async def test_no_leftovers_raises_nothing(self, hass: HomeAssistant):
        entry = _entry(hass)
        _register(hass, entry, CURRENT, object_id="current")

        _async_report_orphaned_entities(hass, entry)

        assert ir.async_get(hass).issues == {}

    async def test_leftovers_raise_a_fixable_issue_that_counts_them(
        self, hass: HomeAssistant
    ):
        entry = _entry(hass)
        _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")
        _register(hass, entry, LEGACY_IMAGE, domain="image", object_id="legacy_image")

        _async_report_orphaned_entities(hass, entry)

        issue = ir.async_get(hass).async_get_issue(
            DOMAIN, f"{ORPHANED_ENTITIES_ISSUE_ID}_{entry.entry_id}"
        )
        assert issue is not None
        assert issue.is_fixable
        assert issue.translation_placeholders["count"] == "2"

    async def test_the_issue_clears_once_they_are_gone(self, hass: HomeAssistant):
        """Otherwise a user who deleted them by hand keeps the repair forever."""
        entry = _entry(hass)
        row = _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")
        _async_report_orphaned_entities(hass, entry)

        er.async_get(hass).async_remove(row.entity_id)
        _async_report_orphaned_entities(hass, entry)

        assert ir.async_get(hass).issues == {}

    async def test_it_survives_a_restart(self, hass: HomeAssistant):
        """It asks the user for a decision, which a restart does not make."""
        entry = _entry(hass)
        _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")
        _async_report_orphaned_entities(hass, entry)

        registry = ir.async_get(hass)
        await flush_store(registry._store)
        reloaded = ir.IssueRegistry(hass)
        await reloaded.async_load()

        issue = reloaded.async_get_issue(
            DOMAIN, f"{ORPHANED_ENTITIES_ISSUE_ID}_{entry.entry_id}"
        )
        assert issue is not None
        assert issue.active


class TestTheFixFlow:
    async def _flow(self, hass, entry):
        flow = await async_create_fix_flow(
            hass,
            f"{ORPHANED_ENTITIES_ISSUE_ID}_{entry.entry_id}",
            {"entry_id": entry.entry_id},
        )
        flow.hass = hass
        return flow

    async def test_nothing_is_deleted_before_the_user_confirms(
        self, hass: HomeAssistant
    ):
        """The whole reason this is a repair and not something setup does."""
        entry = _entry(hass)
        row = _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")

        result = await (await self._flow(hass, entry)).async_step_init()

        assert result["type"] == "form"
        assert er.async_get(hass).async_get(row.entity_id) is not None

    async def test_the_form_names_the_rows_it_would_remove(self, hass: HomeAssistant):
        entry = _entry(hass)
        row = _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")

        result = await (await self._flow(hass, entry)).async_step_init()

        assert row.entity_id in result["description_placeholders"]["entities"]
        assert result["description_placeholders"]["count"] == "1"

    async def test_confirming_removes_the_leftovers_only(self, hass: HomeAssistant):
        entry = _entry(hass)
        legacy = _register(hass, entry, LEGACY_SENSOR, object_id="legacy_sensor")
        current = _register(hass, entry, CURRENT, object_id="current")

        await (await self._flow(hass, entry)).async_step_confirm(user_input={})

        registry = er.async_get(hass)
        assert registry.async_get(legacy.entity_id) is None
        assert registry.async_get(current.entity_id) is not None

    async def test_a_removed_entry_finishes_instead_of_raising(
        self, hass: HomeAssistant
    ):
        """The user may have deleted the entry while the repair sat open."""
        entry = _entry(hass)
        flow = await self._flow(hass, entry)
        await hass.config_entries.async_remove(entry.entry_id)

        result = await flow.async_step_init()

        assert result["type"] == "create_entry"
