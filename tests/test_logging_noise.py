"""The integration must not log what Home Assistant already logs.

A failing poll is reported once by the DataUpdateCoordinator and a failing
setup once by ConfigEntryNotReady. Logging the same failure again at ERROR
doubled every line, and a missing snow table is the normal state of a region
all summer rather than a fault.
"""

import logging

import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.__init__ import async_setup_entry
from custom_components.bergfex.const import COORDINATORS, DOMAIN
from custom_components.bergfex.parser import parse_overview_data
from custom_components.bergfex.unique_id import coordinator_key

AREA_PATH = "/it/test/schneebericht/"


@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={
            "name": "Test Resort",
            "country": "Italien",
            "ski_area": AREA_PATH,
            "language": "it",
            "type": "alpine",
        },
        source="user",
        entry_id="test_entry_id",
    )


class _BrokenSession:
    """Every request fails, the way an outage looks to the coordinator."""

    def get(self, url, *args, **kwargs):
        raise OSError("boom")

    def post(self, url, *args, **kwargs):
        raise OSError("boom")


def _integration_errors(caplog):
    """Errors logged from our own source files.

    Filtering by logger name would not do: the coordinator is handed our
    ``_LOGGER``, so its own single error line carries our logger name. The
    call site is what separates ours from Home Assistant's.
    """
    return [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
        and "custom_components/bergfex" in record.pathname
    ]


def test_a_missing_snow_table_is_not_a_warning(caplog):
    """Regions and cross-country areas have no snow table out of season."""
    caplog.set_level(logging.DEBUG, logger="custom_components.bergfex.parser")

    assert parse_overview_data("<html><body></body></html>") == {}

    messages = [r for r in caplog.records if "table with class" in r.getMessage()]
    assert messages, "the parser should still say why it returned nothing"
    assert all(r.levelno == logging.DEBUG for r in messages)


@pytest.mark.asyncio
async def test_a_failed_poll_is_not_logged_twice(
    hass: HomeAssistant, mock_config_entry, caplog
):
    """The coordinator logs UpdateFailed itself; we must not log it again."""
    caplog.set_level(logging.DEBUG)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_BrokenSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        mock_config_entry.add_to_hass(hass)
        await async_setup_entry(hass, mock_config_entry)

        coordinator = hass.data[DOMAIN][COORDINATORS][coordinator_key(AREA_PATH)]
        caplog.clear()
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert _integration_errors(caplog) == []
    assert any(
        "Error fetching or parsing resort data" in r.getMessage()
        and r.levelno == logging.DEBUG
        for r in caplog.records
    )


@pytest.mark.asyncio
async def test_a_failed_setup_is_not_logged_twice(
    hass: HomeAssistant, mock_config_entry, caplog
):
    """Home Assistant reports ConfigEntryNotReady with its own retry notice."""
    caplog.set_level(logging.DEBUG)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_BrokenSession(),
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        mock_config_entry.add_to_hass(hass)
        caplog.clear()
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)

    assert _integration_errors(caplog) == []
    assert any(
        "Failed to refresh resort coordinator" in r.getMessage()
        and r.levelno == logging.DEBUG
        for r in caplog.records
    )
