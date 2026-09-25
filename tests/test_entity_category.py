"""Only the last-update sensors are diagnostic, and existing installs pick that up.

The last-update sensor reports when bergfex last touched the resort's report. It
says how fresh the other figures are, not what the snow is like, so it belongs
with the diagnostics rather than on an auto-generated dashboard. Every other
entity - status, snow, lifts, slopes, trails, the avalanche warning and the
forecast images - is what a user adds the resort for, and stays primary.

The category is not stored anywhere by this integration. The entity reports it,
and Home Assistant writes it onto the registry entry each time the entity is
added (entity_platform passes entity.entity_category to
EntityRegistry.async_get_or_create, which updates an existing entry in place).
So an install that registered the sensor before it had a category has to come
out of the next setup with the category set and with its entity_id untouched.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.const import DOMAIN, TYPE_ALPINE, TYPE_CROSS_COUNTRY
from custom_components.bergfex.sensor import ALPINE_SENSORS, CROSS_COUNTRY_SENSORS
from custom_components.bergfex.unique_id import build_unique_id

ALPINE_HTML = """
<h2 class="h2-sub">Schneebericht vom 28.10.2024, 21:54</h2>
<dt class="big">Berg (Piste, 3.250m)</dt>
<dd class="big">80 cm</dd>
<dt class="big">Tal (1.200m)</dt>
<dd class="big">40 cm</dd>
<dd>
  <div class="status-lifte" title="open lift"></div>
  5 von 10
</dd>
"""

CROSS_COUNTRY_HTML = (
    Path(__file__).parent / "fixtures" / "cortina_loipen.html"
).read_text(encoding="utf-8")


class MockResponse:
    def __init__(self, text_data, status=200):
        self.status = status
        self._text = text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        pass

    async def text(self):
        return self._text

    def raise_for_status(self):
        pass


class MockSession:
    """Answers every page the coordinator asks for with the same html."""

    def __init__(self, html):
        self._html = html

    def get(self, url, *args, **kwargs):
        return MockResponse(self._html)

    def post(self, url, *args, **kwargs):
        return MockResponse("ok")


def _entry(*, resort_type, path, entry_id):
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Testresort",
        data={
            "name": "Testresort",
            "country": "Österreich",
            "ski_area": path,
            "language": "at",
            "type": resort_type,
        },
        source="user",
        entry_id=entry_id,
        unique_id=path,
    )


async def _setup(hass, entry, html):
    """Run a full entry setup, so the sensors are registered for real."""
    session = MockSession(html)
    with patch(
        "custom_components.bergfex.coordinator.async_get_clientsession",
        return_value=session,
    ), patch(
        "custom_components.bergfex.sensor.async_get_clientsession",
        return_value=session,
    ), patch(
        "custom_components.bergfex.image.async_get_clientsession",
        return_value=session,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize(
    "descriptions",
    [ALPINE_SENSORS, CROSS_COUNTRY_SENSORS],
    ids=["alpine", "cross_country"],
)
def test_only_last_update_is_diagnostic(descriptions):
    """Pin the whole set, so a new category is a decision and not an accident."""
    categories = {d.key: d.entity_category for d in descriptions}

    assert categories.pop("last_update") is EntityCategory.DIAGNOSTIC
    assert set(categories.values()) == {None}


def test_avalanche_warning_stays_primary():
    """It is a safety figure the user wants to see, not metadata about the feed."""
    avalanche = next(d for d in ALPINE_SENSORS if d.key == "avalanche_warning")
    assert avalanche.entity_category is None


@pytest.mark.parametrize(
    ("resort_type", "path", "html"),
    [
        (TYPE_ALPINE, "/achensee/schneebericht/", ALPINE_HTML),
        (TYPE_CROSS_COUNTRY, "/cortina/", CROSS_COUNTRY_HTML),
    ],
    ids=["alpine", "cross_country"],
)
@pytest.mark.asyncio
async def test_existing_entry_becomes_diagnostic_and_keeps_its_ids(
    hass: HomeAssistant, enable_custom_integrations, resort_type, path, html
):
    """A last-update entry registered without a category gets one on setup.

    The entry is created the way an install from before this change has it:
    same unique_id, no entity_category, and an entity_id that is not the one
    the sensor would pick on a fresh install - the user renamed it. Setup must
    update that row in place, not register a second one or rename it back.
    """
    registry = er.async_get(hass)
    entry = _entry(resort_type=resort_type, path=path, entry_id=f"{resort_type}_entry")
    entry.add_to_hass(hass)

    unique_id = build_unique_id(path, "last_update")
    old = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        unique_id,
        suggested_object_id="my_resort_report_time",
        config_entry=entry,
    )
    assert old.entity_category is None
    assert old.entity_id == "sensor.my_resort_report_time"

    await _setup(hass, entry, html)

    updated = registry.async_get(old.entity_id)
    assert updated is not None, "the entity_id changed on setup"
    assert updated.id == old.id
    assert updated.unique_id == unique_id
    assert updated.entity_category is EntityCategory.DIAGNOSTIC
    assert registry.async_get_entity_id("sensor", DOMAIN, unique_id) == old.entity_id

    # The state is still reported under the kept entity_id - that is what the
    # card reads - and no other sensor of the entry picked up a category.
    assert hass.states.get(old.entity_id) is not None
    others = [
        e
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.entity_id != old.entity_id
    ]
    assert others, "the entry registered no other entities"
    assert all(e.entity_category is None for e in others)
