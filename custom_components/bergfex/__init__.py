from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import urljoin

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady


from .const import (
    BASE_URL,
    CONF_COUNTRY,
    CONF_SKI_AREA,
    COORDINATORS,
    COUNTRIES,
    DOMAIN,
)
from .parser import parse_overview_data, parse_resort_page

PLATFORMS = [Platform.SENSOR]
SCAN_INTERVAL = timedelta(minutes=30)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bergfex from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(COORDINATORS, {})

    country_name = entry.data.get(CONF_COUNTRY, "Österreich")
    country_path = COUNTRIES.get(country_name)
    area_name = entry.data["name"]
    area_path = entry.data[CONF_SKI_AREA]

    coordinator = hass.data[DOMAIN][COORDINATORS].get(country_name)

    if coordinator is None:
        _LOGGER.debug("Creating new coordinator for country: %s", country_name)
        session = async_get_clientsession(hass)

        async def async_update_data_country():
            """Fetch and parse data for all ski areas in a country."""
            try:
                url = urljoin(BASE_URL, country_path)
                _LOGGER.debug("Fetching overview data from: %s", url)
                async with session.get(url, allow_redirects=True) as response:
                    response.raise_for_status()
                    html = await response.text()
                parsed_data = parse_overview_data(html)
                _LOGGER.debug("Parsed overview data: %s", parsed_data)
                return parsed_data
            except Exception as err:
                _LOGGER.error("Error fetching or parsing overview data: %s", err)
                raise UpdateFailed(f"Error communicating with Bergfex: {err}") from err

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"bergfex_{country_name}",
            update_method=async_update_data_country,
            update_interval=SCAN_INTERVAL,
        )
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to refresh country coordinator for %s: %s", country_name, err
            )
            raise ConfigEntryNotReady from err
        _LOGGER.debug(
            "Coordinator data after first refresh for %s: %s",
            country_name,
            coordinator.data,
        )
        hass.data[DOMAIN][COORDINATORS][country_name] = coordinator

    if coordinator.data is None or area_path not in coordinator.data:
        resort_coordinator_name = f"bergfex_{area_name}"
        coordinator = hass.data[DOMAIN][COORDINATORS].get(resort_coordinator_name)

        if coordinator is None:
            _LOGGER.debug(
                "Ski area %s not in country data, creating separate coordinator",
                area_name,
            )
            session = async_get_clientsession(hass)

            async def async_update_data_resort():
                """Fetch and parse data for a single ski area."""
                try:
                    url = urljoin(BASE_URL, area_path)
                    _LOGGER.debug("Fetching resort data from: %s", url)
                    async with session.get(url, allow_redirects=True) as response:
                        response.raise_for_status()
                        html = await response.text()
                    parsed_data = parse_resort_page(html)
                    _LOGGER.debug(
                        "Parsed resort data for %s: %s", area_path, parsed_data
                    )
                    return {area_path: parsed_data}
                except Exception as err:
                    _LOGGER.error(
                        "Error fetching or parsing resort data for %s: %s",
                        area_path,
                        err,
                    )
                    raise UpdateFailed(
                        f"Error communicating with Bergfex: {err}"
                    ) from err

            coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name=resort_coordinator_name,
                update_method=async_update_data_resort,
                update_interval=SCAN_INTERVAL,
            )
            try:
                await coordinator.async_config_entry_first_refresh()
            except Exception as err:
                _LOGGER.error(
                    "Failed to refresh resort coordinator for %s: %s", area_name, err
                )
                raise ConfigEntryNotReady from err

            hass.data[DOMAIN][COORDINATORS][resort_coordinator_name] = coordinator

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Forward the unloading to the sensor platform
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
