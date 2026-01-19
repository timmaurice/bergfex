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
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_WEBHOOK_URL,
    CONF_TYPE,
    COORDINATORS,
    COUNTRIES,
    COUNTRIES_CROSS_COUNTRY,
    DOMAIN,
    KEYWORDS,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)
from .parser import (
    parse_cross_country_resort_page,
    parse_cross_country_overview_data,
    parse_overview_data,
    parse_resort_page,
    parse_snow_forecast_images,
)

PLATFORMS = ["sensor", "image"]
SCAN_INTERVAL = timedelta(minutes=30)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bergfex from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(COORDINATORS, {})

    country_name = entry.data.get(CONF_COUNTRY, "Österreich")
    area_name = entry.data["name"]
    area_path = entry.data[CONF_SKI_AREA]
    domain = entry.data.get(CONF_DOMAIN, BASE_URL)
    lang = entry.data.get(CONF_LANGUAGE, "at")
    webhook_url = entry.data.get(CONF_WEBHOOK_URL)
    resort_type = entry.data.get(CONF_TYPE, TYPE_ALPINE)

    if resort_type == TYPE_CROSS_COUNTRY:
        country_path = COUNTRIES_CROSS_COUNTRY.get(country_name)
    else:
        country_path = COUNTRIES.get(country_name)

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

                # For cross-country skiing, ensure we fetch the detailed trail report page
                if resort_type == TYPE_CROSS_COUNTRY:
                    if not url.rstrip("/").endswith("/loipen"):
                        # If the URL ends with a slash, appending "loipen/" works fine with urljoin if we are careful
                        # But urljoin replaces the last component if it doesn't end in slash.
                        # It is safer to modify the path before urljoin or append carefully.
                        fetch_path = area_path
                        if not fetch_path.endswith("/"):
                            fetch_path += "/"
                        url = urljoin(domain, f"{fetch_path}loipen/")

                _LOGGER.debug("Fetching resort data from: %s", url)
                async with session.get(url, allow_redirects=True) as response:
                    response.raise_for_status()
                    html = await response.text()

                parsed_data = {}
                if resort_type == TYPE_CROSS_COUNTRY:
                    parsed_data.update(parse_cross_country_resort_page(html, lang))

                    # Fetch total trail lengths from the overview page, as they are often not on the detail page.
                    if country_path:
                        try:
                            overview_url = urljoin(domain, country_path)
                            _LOGGER.debug(
                                "Fetching cross-country overview from: %s",
                                overview_url,
                            )
                            async with session.get(
                                overview_url, allow_redirects=True
                            ) as response:
                                if response.status == 200:
                                    overview_html = await response.text()
                                    # This will parse totals for all resorts on the page
                                    overview_data = parse_cross_country_overview_data(
                                        overview_html, lang
                                    )
                                    # Find our specific resort in the overview data and update totals
                                    # Find our specific resort in the overview data and update totals
                                    resort_name_from_detail_page = parsed_data.get(
                                        "resort_name"
                                    )
                                    found_match = False
                                    if resort_name_from_detail_page:
                                        try:
                                            trail_report_kw = KEYWORDS.get(
                                                lang, KEYWORDS["at"]
                                            ).get("trail_report", "Loipenbericht")
                                            resort_name_clean = (
                                                resort_name_from_detail_page.replace(
                                                    trail_report_kw, ""
                                                ).strip()
                                            )
                                            # Normalize by taking the first part before any slash
                                            if "/" in resort_name_clean:
                                                resort_name_clean = (
                                                    resort_name_clean.split("/")[
                                                        0
                                                    ].strip()
                                                )

                                            for key, data in overview_data.items():
                                                overview_name = data.get("name", "")
                                                if (
                                                    overview_name
                                                    and resort_name_clean
                                                    in overview_name
                                                ):
                                                    parsed_data.update(data)
                                                    _LOGGER.debug(
                                                        f"Merged overview data for {resort_name_clean} using name matching."
                                                    )
                                                    found_match = True
                                                    break
                                        except Exception as e:
                                            _LOGGER.debug(
                                                f"Name matching for cross-country overview failed: {e}"
                                            )

                                    if not found_match:
                                        _LOGGER.debug(
                                            "Falling back to URL-based matching for cross-country overview."
                                        )
                                        for key, data in overview_data.items():
                                            # Normalize keys and area_path to compare reliably
                                            k_clean = key.strip("/")
                                            ap_clean = area_path.strip("/")
                                            # Match if overview key equals suffix of area_path or vice versa
                                            if k_clean and (
                                                ap_clean.endswith(k_clean)
                                                or k_clean in ap_clean
                                            ):
                                                parsed_data.update(data)
                                                _LOGGER.debug(
                                                    "Merged overview data for %s using URL matching on key %s.",
                                                    area_path,
                                                    key,
                                                )
                                                found_match = True
                                                break
                                else:
                                    _LOGGER.warning(
                                        "Could not fetch cross-country overview page: %s",
                                        response.status,
                                    )
                        except Exception as err:
                            _LOGGER.warning(
                                "Error fetching cross-country overview: %s", err
                            )

                    _LOGGER.debug(
                        "Parsed cross country data for %s: %s", area_path, parsed_data
                    )
                    return {area_path: parsed_data}

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

                # Send data to Webhook
                if webhook_url:
                    try:
                        # copy parsed_data and remove keys that are not string
                        json_data = {
                            k: v
                            for k, v in parsed_data.items()
                            if k not in ("last_update")
                        }
                        async with session.post(
                            webhook_url, json={"merge_variables": json_data}
                        ) as response:
                            _LOGGER.debug("Webhook data sent: %d", response.status)

                    except Exception as err:
                        _LOGGER.error(
                            "Error sending data to webhook %s: %s",
                            webhook_url,
                            err,
                        )

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

    # `entry.runtime_data` is a non-public attribute. Coordinator is stored
    # in `hass.data[DOMAIN][COORDINATORS]` and should be retrieved from there
    # by platforms during setup. Do not set `entry.runtime_data`.

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Forward the unloading to the sensor platform
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
