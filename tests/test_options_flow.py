"""Tests for the options flow: the update interval, and nothing from the entry data.

The language used to be offered here as well, writing the entry's data from an
options flow. It moved to the reconfigure step (see test_reconfigure.py).
"""

import pytest
from unittest.mock import patch

from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.config_flow import OptionsFlowHandler
from custom_components.bergfex.const import (
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)


def _entry(hass: HomeAssistant, options: dict | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Serfaus - Fiss - Ladis",
        data={
            CONF_SKI_AREA: "/serfaus-fiss-ladis/schneebericht/",
            CONF_LANGUAGE: "at",
            CONF_DOMAIN: SUPPORTED_LANGUAGES["at"]["domain"],
            "name": "Serfaus - Fiss - Ladis",
            "url": f"{SUPPORTED_LANGUAGES['at']['domain']}/serfaus-fiss-ladis/schneebericht/",
        },
        options={CONF_UPDATE_INTERVAL: 30} if options is None else options,
    )
    entry.add_to_hass(hass)
    return entry


async def _step(hass: HomeAssistant, entry: MockConfigEntry, user_input=None):
    """Run one options-flow step against `entry`.

    The step has to be awaited inside the patch: OptionsFlow resolves
    `config_entry` lazily, so a coroutine created here and awaited outside would
    hit the real property.
    """
    handler = OptionsFlowHandler()
    handler.hass = hass
    with patch.object(type(handler), "config_entry", entry):
        return await handler.async_step_init(user_input)


def test_core_reloads_the_entry_after_the_options_change():
    """The update listener that used to do this is gone."""
    assert issubclass(OptionsFlowHandler, OptionsFlowWithReload)


@pytest.mark.asyncio
async def test_the_interval_is_stored_in_options(hass: HomeAssistant):
    entry = _entry(hass)
    before = dict(entry.data)

    result = await _step(hass, entry, {CONF_UPDATE_INTERVAL: 45})

    assert result["data"] == {CONF_UPDATE_INTERVAL: 45}
    assert entry.data == before


@pytest.mark.asyncio
async def test_the_form_offers_only_the_interval(hass: HomeAssistant):
    """The language lives in the entry's data, which the reconfigure step writes."""
    entry = _entry(hass, options={CONF_UPDATE_INTERVAL: 90})

    result = await _step(hass, entry)

    schema = result["data_schema"].schema
    assert [str(key) for key in schema] == [CONF_UPDATE_INTERVAL]
    assert next(iter(schema)).default() == 90


@pytest.mark.asyncio
async def test_the_form_defaults_to_the_default_interval(hass: HomeAssistant):
    entry = _entry(hass, options={})

    result = await _step(hass, entry)

    assert next(iter(result["data_schema"].schema)).default() == DEFAULT_UPDATE_INTERVAL
