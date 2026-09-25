"""Unique ids are keyed on the resort path, and existing installs are migrated.

The display name used to key them. It is not unique - bergfex lists more than
one resort under names like "Bergbahnen" - so two such resorts produced the same
unique ids and Home Assistant simply dropped the second one's entities. These
tests pin the new scheme, and above all that switching to it does not orphan the
entities anybody already has.
"""

import pytest
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import bergfex
from custom_components.bergfex.const import DOMAIN
from custom_components.bergfex.coordinator import BergfexCoordinator
from custom_components.bergfex.unique_id import (
    build_unique_id,
    coordinator_key,
    legacy_unique_id_prefixes,
    unique_id_prefix,
)

RESORT_HTML = """
<dt class="big">Berg (Piste, 3.250m)</dt>
<dd class="big">80 cm</dd>
<dt class="big">Tal (1.200m)</dt>
<dd class="big">40 cm</dd>
<dd>
  <div class="status-lifte" title="open lift"></div>
  5 von 10
</dd>
"""


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
    """Answers every page the coordinator asks for with the same resort html."""

    def get(self, url, *args, **kwargs):
        return MockResponse(RESORT_HTML)

    def post(self, url, *args, **kwargs):
        return MockResponse("ok")


def _entry(*, name, path, entry_id):
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title=name,
        data={
            "name": name,
            "country": "Österreich",
            "ski_area": path,
            "language": "at",
            "type": "alpine",
        },
        source="user",
        entry_id=entry_id,
        unique_id=path,
    )


async def _setup(hass, entry):
    """Run a full entry setup, the way Home Assistant runs one.

    Going through async_setup manages the entry state and the config-entry
    context var, which is what lets the coordinator's first refresh run and the
    sensor and image platforms actually be forwarded. Registering entities for
    real is the point: a migration that is only ever called on an empty registry
    proves nothing.
    """
    if entry.entry_id not in hass.config_entries._entries:
        entry.add_to_hass(hass)
    with patch(
        "custom_components.bergfex.coordinator.async_get_clientsession",
        return_value=MockSession(),
    ), patch(
        "custom_components.bergfex.sensor.async_get_clientsession",
        return_value=MockSession(),
    ), patch(
        "custom_components.bergfex.image.async_get_clientsession",
        return_value=MockSession(),
    ):
        if entry.state is not ConfigEntryState.LOADED:
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    # Setting the component up brings up every entry it already has, so an entry
    # added before the first _setup call may be loaded by that call. Either way
    # it has to be up before a test looks at the registry.
    assert entry.state is ConfigEntryState.LOADED


async def _restart(hass, entry):
    """Unload and set the entry up again, standing in for a Home Assistant restart."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await _setup(hass, entry)


def test_prefix_is_the_path_not_the_name():
    """The path goes in verbatim, so no two paths can fold onto one prefix."""
    assert unique_id_prefix("/ischgl/schneebericht/") == "bergfex_ischgl/schneebericht_"

    # Slugifying the path would collapse both of these to "bergfex_a_b_".
    assert unique_id_prefix("/a-b/") != unique_id_prefix("/a/b/")


def test_legacy_prefixes_cover_both_old_schemes():
    """sensor.py slugified the name; image.py lowercased and replaced spaces."""
    prefixes = legacy_unique_id_prefixes("Feldberg / Hochschwarzwald")

    assert "bergfex_feldberg_hochschwarzwald_" in prefixes
    assert "bergfex_feldberg_/_hochschwarzwald_" in prefixes

    # A plain name needs only one prefix, and must not be listed twice.
    assert legacy_unique_id_prefixes("Achensee") == ("bergfex_achensee_",)


@pytest.mark.asyncio
async def test_fresh_install_gets_path_based_ids(
    hass: HomeAssistant, enable_custom_integrations
):
    """A brand new resort registers its entities under the resort path."""
    entry = _entry(
        name="Achensee", path="/achensee/schneebericht/", entry_id="fresh_entry"
    )
    await _setup(hass, entry)

    registry = er.async_get(hass)
    entries = registry.entities.get_entries_for_config_entry_id(entry.entry_id)
    assert entries, "the entry registered no entities at all"

    prefix = unique_id_prefix("/achensee/schneebericht/")
    for registry_entry in entries:
        assert registry_entry.unique_id.startswith(prefix)

    assert registry.async_get_entity_id(
        "sensor", DOMAIN, build_unique_id("/achensee/schneebericht/", "status")
    )


@pytest.mark.asyncio
async def test_existing_install_keeps_its_entity_ids(
    hass: HomeAssistant, enable_custom_integrations
):
    """The migration rewrites the id in place and leaves the entity alone.

    Keeping the registry entry is the whole point: the recorder keys a state
    history and its statistics off the entity_id, and every dashboard and
    automation names it too. So the assertion is that the same registry row -
    same row id, same entity_id, same name the user gave it - now carries the
    new unique id.
    """
    registry = er.async_get(hass)
    entry = _entry(
        name="Achensee", path="/achensee/schneebericht/", entry_id="existing_entry"
    )
    entry.add_to_hass(hass)

    legacy = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "bergfex_achensee_status",
        suggested_object_id="achensee_status",
        config_entry=entry,
    )
    registry.async_update_entity(legacy.entity_id, name="Snow at the hut")
    assert legacy.entity_id == "sensor.achensee_status"

    await _setup(hass, entry)

    migrated = registry.async_get("sensor.achensee_status")
    assert migrated is not None, "the entity was orphaned by the migration"
    assert migrated.id == legacy.id
    assert migrated.name == "Snow at the hut"
    assert migrated.unique_id == build_unique_id("/achensee/schneebericht/", "status")
    assert migrated.previous_unique_id == "bergfex_achensee_status"

    # And nothing was registered alongside it under the new id.
    assert (
        registry.async_get_entity_id("sensor", DOMAIN, migrated.unique_id)
        == "sensor.achensee_status"
    )


@pytest.mark.asyncio
async def test_migration_covers_the_image_scheme(
    hass: HomeAssistant, enable_custom_integrations
):
    """Images were registered under a name variant of their own."""
    registry = er.async_get(hass)
    entry = _entry(
        name="Feldberg / Hochschwarzwald",
        path="/feldberg/schneebericht/",
        entry_id="image_entry",
    )
    entry.add_to_hass(hass)

    legacy = registry.async_get_or_create(
        "image",
        DOMAIN,
        "bergfex_feldberg_/_hochschwarzwald_forecast_image_day_0",
        suggested_object_id="feldberg_hochschwarzwald_forecast_image_day_0",
        config_entry=entry,
    )

    await _setup(hass, entry)

    migrated = registry.async_get(legacy.entity_id)
    assert migrated is not None
    assert migrated.unique_id == build_unique_id(
        "/feldberg/schneebericht/", "forecast_image_day_0"
    )


@pytest.mark.asyncio
async def test_same_display_name_no_longer_collides(
    hass: HomeAssistant, enable_custom_integrations
):
    """Two resorts sharing a name each keep their own entities.

    Under the name-based scheme both produced "bergfex_bergbahnen_status", and
    the second resort's entity was refused with "Unique id already in use".
    """
    first = _entry(name="Bergbahnen", path="/first-valley/schneebericht/", entry_id="a")
    second = _entry(
        name="Bergbahnen", path="/second-valley/schneebericht/", entry_id="b"
    )

    await _setup(hass, first)
    await _setup(hass, second)

    registry = er.async_get(hass)
    status_a = registry.async_get_entity_id(
        "sensor", DOMAIN, build_unique_id("/first-valley/schneebericht/", "status")
    )
    status_b = registry.async_get_entity_id(
        "sensor", DOMAIN, build_unique_id("/second-valley/schneebericht/", "status")
    )

    assert status_a is not None
    assert status_b is not None
    assert status_a != status_b


@pytest.mark.asyncio
async def test_migration_is_idempotent(hass: HomeAssistant, enable_custom_integrations):
    """Restarting must not migrate an already migrated entity a second time."""
    registry = er.async_get(hass)
    entry = _entry(
        name="Achensee", path="/achensee/schneebericht/", entry_id="idempotent_entry"
    )
    entry.add_to_hass(hass)

    registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "bergfex_achensee_status",
        suggested_object_id="achensee_status",
        config_entry=entry,
    )

    await _setup(hass, entry)
    after_first = registry.async_get("sensor.achensee_status")
    assert after_first is not None

    # A second restart. The ids no longer match any legacy prefix, so the
    # migration has nothing to do - and must not, for instance, treat the new id
    # as legacy and prefix it again.
    await _restart(hass, entry)

    after_second = registry.async_get("sensor.achensee_status")
    assert after_second is not None
    assert after_second.id == after_first.id
    assert after_second.unique_id == after_first.unique_id
    assert after_second.previous_unique_id == "bergfex_achensee_status"


@pytest.mark.asyncio
async def test_duplicate_entries_do_not_abort_setup(
    hass: HomeAssistant, enable_custom_integrations
):
    """The leftover of a duplicated resort keeps its old ids rather than failing.

    Two entries for one resort is the situation the duplicate repair issue
    exists for. They can carry different display names - one picked from the
    list, one typed in by hand - so their entities sit under different legacy
    prefixes, and both of those migrate onto the same path-based ids. The
    registry refuses the second with a ValueError, and an exception here would
    take the whole entry setup down with it.
    """
    registry = er.async_get(hass)
    winner = _entry(name="Achensee", path="/achensee/schneebericht/", entry_id="win")
    # The leftover keeps unique_id None, which is exactly what the backfill in
    # __init__.py leaves it with.
    leftover = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Achensee Bergbahnen",
        data={**winner.data, "name": "Achensee Bergbahnen"},
        source="user",
        entry_id="left",
    )

    winner.add_to_hass(hass)
    leftover.add_to_hass(hass)
    registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "bergfex_achensee_status",
        suggested_object_id="achensee_status",
        config_entry=winner,
    )
    stale = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "bergfex_achensee_bergbahnen_status",
        suggested_object_id="achensee_bergbahnen_status",
        config_entry=leftover,
    )

    await _setup(hass, winner)
    await _setup(hass, leftover)

    # The winner took the path-based id; the leftover kept the one it had.
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, build_unique_id("/achensee/schneebericht/", "status")
        )
        == "sensor.achensee_status"
    )
    survivor = registry.async_get(stale.entity_id)
    assert survivor is not None
    assert survivor.unique_id == "bergfex_achensee_bergbahnen_status"


@pytest.mark.asyncio
async def test_same_name_resorts_get_their_own_coordinator(
    hass: HomeAssistant, enable_custom_integrations
):
    """Sharing a name must not mean sharing a coordinator.

    The coordinator store was keyed on the display name as well, so the second
    resort found the first one's coordinator already there and reused it - and a
    coordinator only ever fetches the path it was built for. Both resorts then
    reported the first one's snow.
    """
    first = _entry(name="Bergbahnen", path="/first-valley/schneebericht/", entry_id="a")
    second = _entry(
        name="Bergbahnen", path="/second-valley/schneebericht/", entry_id="b"
    )

    await _setup(hass, first)
    await _setup(hass, second)

    first_coordinator = first.runtime_data
    second_coordinator = second.runtime_data

    assert first_coordinator is not second_coordinator
    assert "/first-valley/schneebericht/" in first_coordinator.data
    assert "/second-valley/schneebericht/" in second_coordinator.data


@pytest.mark.asyncio
async def test_the_coordinator_lives_on_the_entry(
    hass: HomeAssistant, enable_custom_integrations
):
    """The coordinator is the entry's runtime_data, and goes with the entry.

    It used to sit in hass.data[DOMAIN], which unload had to pop by hand. Nothing
    of this integration is kept there any more.
    """
    entry = _entry(name="Achensee", path="/achensee/schneebericht/", entry_id="a")

    await _setup(hass, entry)

    coordinator = entry.runtime_data
    assert isinstance(coordinator, DataUpdateCoordinator)
    assert coordinator.config_entry is entry
    assert coordinator.name == coordinator_key("/achensee/schneebericht/")
    assert "/achensee/schneebericht/" in coordinator.data
    assert DOMAIN not in hass.data

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert not hasattr(entry, "runtime_data")
    assert DOMAIN not in hass.data


@pytest.mark.asyncio
async def test_runtime_data_is_the_bergfex_coordinator(
    hass: HomeAssistant, enable_custom_integrations
):
    """Setup stores the integration's own coordinator class, not a bare one.

    The platforms are typed against BergfexCoordinator through
    BergfexConfigEntry, which is still importable from the package root.
    """
    entry = _entry(name="Achensee", path="/achensee/schneebericht/", entry_id="a")

    await _setup(hass, entry)

    assert type(entry.runtime_data) is BergfexCoordinator
    assert bergfex.BergfexConfigEntry.__value__ == ConfigEntry[BergfexCoordinator]


@pytest.mark.asyncio
async def test_duplicate_entries_keep_their_own_coordinator(
    hass: HomeAssistant, enable_custom_integrations
):
    """A second entry for one resort must not live off the first one's coordinator.

    The shared store handed the leftover the winner's coordinator, which belongs
    to the winner's config entry. Unloading the winner - a reload after changing
    its options is enough - shut that coordinator down, and the leftover's
    entities never updated again.
    """
    winner = _entry(name="Achensee", path="/achensee/schneebericht/", entry_id="win")
    leftover = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Achensee",
        data=dict(winner.data),
        source="user",
        entry_id="left",
    )
    winner.add_to_hass(hass)
    leftover.add_to_hass(hass)

    await _setup(hass, winner)
    await _setup(hass, leftover)

    assert winner.runtime_data is not leftover.runtime_data
    assert leftover.runtime_data.config_entry is leftover

    assert await hass.config_entries.async_unload(winner.entry_id)
    await hass.async_block_till_done()

    fetched = []
    get = MockSession.get

    def _counting_get(self, url, *args, **kwargs):
        fetched.append(url)
        return get(self, url, *args, **kwargs)

    with patch.object(MockSession, "get", _counting_get):
        await leftover.runtime_data.async_refresh()

    assert fetched, "the leftover's coordinator was shut down with the winner"
    assert leftover.runtime_data.last_update_success
