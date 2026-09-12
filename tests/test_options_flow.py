"""Tests for changing a resort's language after setup."""

import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.config_flow import OptionsFlowHandler
from custom_components.bergfex.const import (
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)


def _entry(hass: HomeAssistant, language: str = "at") -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Serfaus - Fiss - Ladis",
        data={
            CONF_SKI_AREA: "/serfaus-fiss-ladis/schneebericht/",
            CONF_LANGUAGE: language,
            CONF_DOMAIN: SUPPORTED_LANGUAGES[language]["domain"],
            "name": "Serfaus - Fiss - Ladis",
            "url": f"{SUPPORTED_LANGUAGES[language]['domain']}/serfaus-fiss-ladis/schneebericht/",
        },
        options={CONF_UPDATE_INTERVAL: 30},
    )
    entry.add_to_hass(hass)
    return entry


async def _submit(hass: HomeAssistant, entry: MockConfigEntry, user_input: dict):
    """Run one options-flow submission against `entry`.

    The step has to be awaited inside the patch: OptionsFlow resolves
    `config_entry` lazily, so a coroutine created here and awaited outside would
    hit the real property.
    """
    handler = OptionsFlowHandler()
    handler.hass = hass
    with patch.object(type(handler), "config_entry", entry):
        return await handler.async_step_init(user_input)


@pytest.mark.asyncio
async def test_language_change_moves_domain_and_url(hass: HomeAssistant):
    """The language selects the domain, and the entry caches a url built from it."""
    entry = _entry(hass, "at")
    await _submit(hass, entry, {CONF_UPDATE_INTERVAL: 30, CONF_LANGUAGE: "fr"})

    assert entry.data[CONF_LANGUAGE] == "fr"
    assert entry.data[CONF_DOMAIN] == SUPPORTED_LANGUAGES["fr"]["domain"]
    assert entry.data["url"].startswith(SUPPORTED_LANGUAGES["fr"]["domain"])
    assert entry.data["url"].endswith("/serfaus-fiss-ladis/schneebericht/")


@pytest.mark.asyncio
async def test_resort_path_survives_the_switch(hass: HomeAssistant):
    """Resort paths are identical on every bergfex domain and must not be rewritten."""
    entry = _entry(hass, "at")
    await _submit(hass, entry, {CONF_UPDATE_INTERVAL: 30, CONF_LANGUAGE: "pl"})

    assert entry.data[CONF_SKI_AREA] == "/serfaus-fiss-ladis/schneebericht/"


@pytest.mark.asyncio
async def test_keeping_the_language_leaves_the_entry_alone(hass: HomeAssistant):
    entry = _entry(hass, "at")
    before = dict(entry.data)

    result = await _submit(hass, entry, {CONF_UPDATE_INTERVAL: 45, CONF_LANGUAGE: "at"})

    assert entry.data == before
    assert result["data"][CONF_UPDATE_INTERVAL] == 45


@pytest.mark.asyncio
async def test_update_interval_is_still_stored_in_options(hass: HomeAssistant):
    """The language belongs in data, the interval in options - do not mix them."""
    entry = _entry(hass, "at")
    result = await _submit(hass, entry, {CONF_UPDATE_INTERVAL: 15, CONF_LANGUAGE: "it"})

    assert result["data"] == {CONF_UPDATE_INTERVAL: 15}
    assert CONF_LANGUAGE not in result["data"]
    assert entry.data[CONF_LANGUAGE] == "it"


@pytest.mark.asyncio
async def test_form_offers_every_supported_language(hass: HomeAssistant):
    entry = _entry(hass, "at")
    handler = OptionsFlowHandler()
    handler.hass = hass
    with patch.object(type(handler), "config_entry", entry):
        result = await handler.async_step_init()

    schema = result["data_schema"].schema
    language_key = next(k for k in schema if str(k) == CONF_LANGUAGE)
    assert set(schema[language_key].container) == set(SUPPORTED_LANGUAGES)
    assert language_key.default() == "at"
