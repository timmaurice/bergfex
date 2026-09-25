"""Reconfigure: moving an existing entry to another bergfex language.

The entry is set up through Home Assistant against the captured Serfaus pages,
which exist for every language, and the flow is driven through the real flow
manager. The HTTP layer is mocked with ``aioclient_mock``, as in
test_diagnostics.py, so the reload after a successful switch really polls the
new domain.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex import coordinator
from custom_components.bergfex.const import (
    CONF_COUNTRY,
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_TYPE,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    SUPPORTED_LANGUAGES,
    TYPE_CROSS_COUNTRY,
)
from custom_components.bergfex.coordinator import detail_page_url

FIXTURES = Path(__file__).parent / "fixtures"
TRANSLATIONS = (
    Path(__file__).parent.parent / "custom_components" / "bergfex" / "translations"
)

AREA_PATH = "/serfaus-fiss-ladis/schneebericht/"
AT = SUPPORTED_LANGUAGES["at"]["domain"]
EN = SUPPORTED_LANGUAGES["en"]["domain"]


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Serfaus - Fiss - Ladis",
        data={
            "name": "Serfaus - Fiss - Ladis",
            CONF_COUNTRY: "Österreich",
            CONF_SKI_AREA: AREA_PATH,
            CONF_LANGUAGE: "at",
            CONF_DOMAIN: AT,
            "url": f"{AT}{AREA_PATH}",
            CONF_TYPE: "alpine",
            "webhook_url": None,
        },
        options={CONF_UPDATE_INTERVAL: 30},
        source="user",
        entry_id="serfaus",
        unique_id=AREA_PATH,
    )


def _mock_bergfex(aioclient_mock, *, english_page: dict | None = None) -> None:
    """Serve Serfaus on bergfex.at and, unless overridden, on bergfex.com.

    First match wins, so the catch-all comes last.
    """
    aioclient_mock.get(
        re.compile(re.escape(f"{AT}{AREA_PATH}") + "$"),
        text=_fixture("serfaus-at.html"),
    )
    aioclient_mock.get(
        re.compile(re.escape(f"{EN}{AREA_PATH}") + "$"),
        **(english_page or {"text": _fixture("serfaus-en.html")}),
    )
    aioclient_mock.get(re.compile(r"."), text="<html></html>")


def _requested(aioclient_mock, domain: str) -> int:
    """Count the requests made for the area page on `domain`."""
    return sum(
        1
        for _method, url, *_ in aioclient_mock.mock_calls
        if str(url) == domain + AREA_PATH
    )


def _identity(hass: HomeAssistant, entry: MockConfigEntry):
    """Everything a language switch must leave alone."""
    entities = sorted(
        (row.unique_id, row.entity_id)
        for row in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    )
    devices = sorted(
        (device.id, tuple(sorted(device.identifiers)))
        for device in dr.async_entries_for_config_entry(
            dr.async_get(hass), entry.entry_id
        )
    )
    return entry.unique_id, entities, devices


@pytest.fixture(autouse=True)
def _empty_poll_caches():
    """The caches are module state, so a test must not inherit another's entries."""
    coordinator._FORECAST_CACHE.clear()
    coordinator._SEASON_PANEL_CACHE.clear()
    yield
    coordinator._FORECAST_CACHE.clear()
    coordinator._SEASON_PANEL_CACHE.clear()


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_form_offers_every_language_with_the_current_one_selected(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"] == {"name": "Serfaus - Fiss - Ladis"}
    schema = result["data_schema"].schema
    language_key = next(key for key in schema if str(key) == CONF_LANGUAGE)
    assert set(schema[language_key].container) == set(SUPPORTED_LANGUAGES)
    assert language_key.default() == "at"
    # Language is the one field: nothing else about the entry depends on it.
    assert [str(key) for key in schema] == [CONF_LANGUAGE]


async def test_switching_language_keeps_every_identity_and_reloads(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)
    before = _identity(hass, entry)
    assert before[1], "the setup registered no entities to compare"
    assert before[2], "the setup registered no device to compare"
    old_coordinator = entry.runtime_data
    old_data = dict(entry.data)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "en"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # The language, the domain it selects and the url built from it move ...
    assert entry.data[CONF_LANGUAGE] == "en"
    assert entry.data[CONF_DOMAIN] == EN
    assert entry.data["url"] == f"{EN}{AREA_PATH}"
    # ... and nothing else in the entry does.
    moved = {CONF_LANGUAGE, CONF_DOMAIN, "url"}
    assert {k: v for k, v in entry.data.items() if k not in moved} == {
        k: v for k, v in old_data.items() if k not in moved
    }
    assert entry.title == "Serfaus - Fiss - Ladis"
    assert entry.options == {CONF_UPDATE_INTERVAL: 30}

    # Reloaded: a new coordinator, polling the new domain in the new language.
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not old_coordinator
    assert entry.runtime_data._domain == EN
    assert entry.runtime_data._lang == "en"
    assert entry.runtime_data.last_update_success
    # Once by the flow's check, once by the reloaded coordinator.
    assert _requested(aioclient_mock, EN) == 2

    # Entry unique id, entity unique ids and entity ids, device and identifiers.
    assert _identity(hass, entry) == before


async def test_a_page_the_new_domain_does_not_serve_changes_nothing(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock, english_page={"status": 404})
    entry = _entry()
    await _setup(hass, entry)
    old_coordinator = entry.runtime_data
    old_data = dict(entry.data)
    before = _identity(hass, entry)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "en"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}
    # The form keeps what the user picked, so a retry is one click.
    language_key = next(
        key for key in result["data_schema"].schema if str(key) == CONF_LANGUAGE
    )
    assert language_key.default() == "en"

    assert dict(entry.data) == old_data
    assert entry.runtime_data is old_coordinator
    assert entry.state is ConfigEntryState.LOADED
    assert _identity(hass, entry) == before


async def test_no_connection_to_the_new_domain_changes_nothing(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock, english_page={"exc": TimeoutError()})
    entry = _entry()
    await _setup(hass, entry)
    old_data = dict(entry.data)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "en"}
    )

    assert result["errors"] == {"base": "cannot_connect"}
    assert dict(entry.data) == old_data


async def test_keeping_the_language_does_not_reload(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)
    old_coordinator = entry.runtime_data
    old_data = dict(entry.data)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "at"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert dict(entry.data) == old_data
    assert entry.runtime_data is old_coordinator


async def test_an_entry_deleted_while_the_form_is_open_aborts(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)

    result = await entry.start_reconfigure_flow(hass)
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "en"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown_entry"
    assert hass.config_entries.async_get_entry(entry.entry_id) is None


async def test_changing_the_interval_reloads_through_the_options_flow(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock
):
    """The reload moved from an update listener to OptionsFlowWithReload.

    Core refuses the two together with a ValueError, and reports an update
    listener next to async_update_reload_and_abort, so this also guards against
    one being added back.
    """
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)
    assert not entry.update_listeners
    old_coordinator = entry.runtime_data

    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema_keys = [str(key) for key in result["data_schema"].schema]
    assert schema_keys == [CONF_UPDATE_INTERVAL]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_INTERVAL: 60}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_UPDATE_INTERVAL: 60}
    assert entry.runtime_data is not old_coordinator
    assert entry.runtime_data.update_interval.total_seconds() == 60 * 60


@pytest.mark.parametrize(
    ("area_path", "resort_type", "expected"),
    [
        (AREA_PATH, "alpine", f"{EN}{AREA_PATH}"),
        (
            "/venetien/langlaufen/cortina-ampezzo/",
            TYPE_CROSS_COUNTRY,
            f"{EN}/venetien/langlaufen/cortina-ampezzo/loipen/",
        ),
        (
            "/venetien/langlaufen/cortina-ampezzo",
            TYPE_CROSS_COUNTRY,
            f"{EN}/venetien/langlaufen/cortina-ampezzo/loipen/",
        ),
        (
            "/venetien/langlaufen/cortina-ampezzo/loipen/",
            TYPE_CROSS_COUNTRY,
            f"{EN}/venetien/langlaufen/cortina-ampezzo/loipen/",
        ),
    ],
)
def test_the_checked_page_is_the_one_the_coordinator_polls(
    area_path, resort_type, expected
):
    """A cross-country area is read off its trail report, so that is checked."""
    assert detail_page_url(EN, area_path, resort_type) == expected


def test_every_language_translates_the_reconfigure_step():
    """A missing key falls back to English, a stray one is dead weight."""

    def shape(path: Path):
        config = json.loads(path.read_text(encoding="utf-8"))["config"]
        step = config["step"]["reconfigure"]
        return (
            sorted(step),
            sorted(step["data"]),
            sorted(step["data_description"]),
            sorted(config["abort"]),
            sorted(config["error"]),
        )

    reference = shape(TRANSLATIONS / "en.json")
    assert (
        "{name}"
        in json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8"))["config"][
            "step"
        ]["reconfigure"]["description"]
    )
    for path in sorted(TRANSLATIONS.glob("*.json")):
        assert shape(path) == reference, f"{path.name} does not match en.json"
        description = json.loads(path.read_text(encoding="utf-8"))["config"]["step"][
            "reconfigure"
        ]["description"]
        assert "{name}" in description, f"{path.name} drops the {{name}} placeholder"
