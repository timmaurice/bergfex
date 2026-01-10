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

import requests

from .const import (
    BASE_URL,
    CONF_COUNTRY,
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_WEBHOOK_URL,
    COORDINATORS,
    COUNTRIES,
    DOMAIN,
)
from .parser import parse_overview_data, parse_resort_page, parse_snow_forecast_images

PLATFORMS = ["sensor", "image"]
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
    domain = entry.data.get(CONF_DOMAIN, BASE_URL)
    lang = entry.data.get(CONF_LANGUAGE, "at")
    webhook_url = entry.data.get(CONF_WEBHOOK_URL)

    # Always create a resort-specific coordinator to get detail page data
    resort_coordinator_name = f"bergfex_{area_name}"
    coordinator = hass.data[DOMAIN][COORDINATORS].get(resort_coordinator_name)

    if coordinator is None:
        _LOGGER.debug(
            "Creating resort coordinator for %s to fetch detail page", area_name
        )
        session = async_get_clientsession(hass)

        async def async_update_data_resort():
            """Fetch and parse data for a single ski area from detail page."""
            try:
                url = urljoin(domain, area_path)
                _LOGGER.debug("Fetching resort data from: %s", url)
                async with session.get(url, allow_redirects=True) as response:
                    response.raise_for_status()
                    html = await response.text()
                parsed_data = parse_resort_page(html, area_path, lang)

                # Fetch "New Snow" from region overview (more accurate than detail page)
                region_path_from_data = parsed_data.get("region_path", "").strip("/")
                if region_path_from_data:
                    try:
                        # Construct URL for region snow report (e.g. /tirol/schneewerte/)
                        snow_report_url = urljoin(
                            domain, f"/{region_path_from_data}/schneewerte/"
                        )
                        _LOGGER.debug(
                            "Fetching region snow report from: %s", snow_report_url
                        )
                        async with session.get(
                            snow_report_url, allow_redirects=True
                        ) as response:
                            if response.status == 200:
                                overview_html = await response.text()
                                overview_data = parse_overview_data(overview_html, lang)
                                # The keys in overview_data are full paths e.g. /skimountaineering/tirol/hintertux/
                                # area_path is e.g. /hintertux/
                                # We need to find the matching entry
                                for key, data in overview_data.items():
                                    if area_path.strip("/") in key:
                                        if "new_snow" in data:
                                            parsed_data["new_snow"] = data["new_snow"]
                                            _LOGGER.debug(
                                                "Updated new_snow from overview: %s",
                                                parsed_data["new_snow"],
                                            )
                                        break
                            else:
                                _LOGGER.warning(
                                    "Could not fetch region snow report: %s",
                                    response.status,
                                )
                    except Exception as err:
                        _LOGGER.warning("Error fetching region snow report: %s", err)

                # Fetch snow forecast images (pages 0-5)
                for i in range(6):
                    try:
                        # Construct URL for forecast page using region_path
                        region_path_from_data = parsed_data.get(
                            "region_path", ""
                        ).strip("/")
                        if region_path_from_data:
                            forecast_url = urljoin(
                                domain,
                                f"/{region_path_from_data}/wetter/schneevorhersage/{i}/",
                            )
                        else:
                            _LOGGER.warning(
                                "Region path not found for %s, cannot fetch forecast images.",
                                area_path,
                            )
                            continue
                        _LOGGER.debug("Fetching forecast images from: %s", forecast_url)
                        async with session.get(
                            forecast_url, allow_redirects=True
                        ) as response:
                            if response.status == 200:
                                forecast_html = await response.text()
                                image_data = parse_snow_forecast_images(
                                    forecast_html, i
                                )

                                # Flatten data into parsed_data
                                if "daily_forecast_url" in image_data:
                                    parsed_data[f"forecast_image_day_{i}_url"] = (
                                        image_data["daily_forecast_url"]
                                    )
                                    parsed_data[f"forecast_image_day_{i}_caption"] = (
                                        image_data.get("daily_caption", "")
                                    )

                                if "summary_url" in image_data:
                                    hours = (i + 1) * 24
                                    parsed_data[f"summary_image_{hours}h_url"] = (
                                        image_data["summary_url"]
                                    )
                                    parsed_data[f"summary_image_{hours}h_caption"] = (
                                        image_data.get("summary_caption", "")
                                    )
                            else:
                                _LOGGER.warning(
                                    "Could not fetch forecast page %d: %s",
                                    i,
                                    response.status,
                                )
                    except Exception as err:
                        _LOGGER.warning("Error fetching forecast page %d: %s", i, err)

                _LOGGER.debug("Parsed resort data for %s: %s", area_path, parsed_data)

                requests.post(webhook_url, json={area_path: parsed_data})

                return {area_path: parsed_data}
            except Exception as err:
                _LOGGER.error(
                    "Error fetching or parsing resort data for %s: %s",
                    area_path,
                    err,
                )
                raise UpdateFailed(f"Error communicating with Bergfex: {err}") from err

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
