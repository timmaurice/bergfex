"""The resort coordinator: one per config entry, polling that entry's ski area."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any
from urllib.parse import urljoin

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BASE_URL,
    CONF_COUNTRY,
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_TYPE,
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_URL,
    COUNTRIES,
    COUNTRIES_CROSS_COUNTRY,
    DEFAULT_UPDATE_INTERVAL,
    KEYWORDS,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)
from .parser import (
    evaluate_status,
    parse_cross_country_overview_data,
    parse_cross_country_resort_page,
    parse_overview_data,
    parse_resort_page,
    parse_snow_forecast_images,
)
from .unique_id import coordinator_key

# The package's logger, not this module's: the coordinator logs its own fetch
# and failure lines through it, and they have always carried the integration's
# name.
_LOGGER = logging.getLogger(__package__)

# An entry's runtime_data is its resort coordinator, whose data is keyed on the
# area path: {area_path: parsed_data}.
type BergfexConfigEntry = ConfigEntry[BergfexCoordinator]

# Winter and summer operating periods live only on a resort's main page, and they
# change at most once a season. Caching them keeps this from costing an extra
# request on every poll - bergfex rate-limits, and the subpage is fetched anyway.
_SEASON_PANEL_CACHE: dict[str, dict[str, Any]] = {}

_SEASON_PANEL_KEYS = (
    "winter_season_start",
    "winter_season_end",
    "winter_operating_hours_start",
    "winter_operating_hours_end",
    "summer_season_start",
    "summer_season_end",
    "summer_operating_hours_start",
    "summer_operating_hours_end",
)

# A region's forecast pages are the same for every resort in it, so they are
# keyed on the url and shared across coordinators. The TTL is generous: bergfex
# republishes these graphics a few times a day.
_FORECAST_CACHE: dict[str, tuple[float, dict[str, str]]] = {}
_FORECAST_CACHE_TTL = 10 * 60


def detail_page_url(domain: str, area_path: str, resort_type: str) -> str:
    """Return the page a poll reads an area from.

    A ski resort is read off its own path. A cross-country area is read off its
    trail report, the "loipen/" page under the area path, unless the path names
    that page already. The config flow checks the same url before it moves an
    entry to another domain, so both have to agree on it.
    """
    url = urljoin(domain, area_path)
    if resort_type == TYPE_CROSS_COUNTRY and not url.rstrip("/").endswith("/loipen"):
        # urljoin replaces the last segment of a path without a trailing slash,
        # so the slash has to be there before "loipen/" is joined on.
        fetch_path = area_path if area_path.endswith("/") else f"{area_path}/"
        url = urljoin(domain, f"{fetch_path}loipen/")
    return url


async def _async_forecast_images(
    hass: HomeAssistant, session, forecast_url: str, page: int
) -> dict[str, str] | None:
    """Return one region forecast page's images, fetching it at most once per TTL.

    Forecast pages are per region, so the work grows with the number of regions
    rather than of resorts. Returns None when the page could not be read.
    """
    cached = _FORECAST_CACHE.get(forecast_url)
    if cached is not None and (time.monotonic() - cached[0]) < _FORECAST_CACHE_TTL:
        _LOGGER.debug("Reusing cached forecast page: %s", forecast_url)
        return cached[1]

    _LOGGER.debug("Fetching forecast images from: %s", forecast_url)
    async with session.get(forecast_url, allow_redirects=True) as response:
        if response.status != 200:
            _LOGGER.warning(
                "Could not fetch forecast page %d: %s", page, response.status
            )
            return None
        forecast_html = await response.text()

    image_data = await hass.async_add_executor_job(
        parse_snow_forecast_images, forecast_html, page
    )
    _FORECAST_CACHE[forecast_url] = (time.monotonic(), image_data)
    return image_data


class BergfexCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch one ski area's detail page, plus the region pages it draws on.

    Always a coordinator of its own. It belongs to its entry alone: a second
    entry for the same resort used to borrow the first one's, and unloading the
    first shut it down under both.
    """

    config_entry: BergfexConfigEntry

    def __init__(self, hass: HomeAssistant, entry: BergfexConfigEntry) -> None:
        """Read the entry's resort settings and schedule the polls."""
        country_name = entry.data.get(CONF_COUNTRY, "Österreich")
        self._area_path: str = entry.data[CONF_SKI_AREA]
        self._domain: str = entry.data.get(CONF_DOMAIN, BASE_URL)
        self._lang: str = entry.data.get(CONF_LANGUAGE, "at")
        self._webhook_url: str | None = entry.data.get(CONF_WEBHOOK_URL)
        self._resort_type: str = entry.data.get(CONF_TYPE, TYPE_ALPINE)

        if self._resort_type == TYPE_CROSS_COUNTRY:
            self._country_path = COUNTRIES_CROSS_COUNTRY.get(country_name)
        else:
            self._country_path = COUNTRIES.get(country_name)

        self._session = async_get_clientsession(hass)

        update_interval_minutes = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=coordinator_key(self._area_path),
            update_interval=timedelta(minutes=update_interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch and parse data for a single ski area from detail page."""
        # Bound to the names the update was written against when it was a
        # closure in async_setup_entry, so the body reads as it always did.
        hass = self.hass
        session = self._session
        area_path = self._area_path
        domain = self._domain
        lang = self._lang
        webhook_url = self._webhook_url
        resort_type = self._resort_type
        country_path = self._country_path

        try:
            url = detail_page_url(domain, area_path, resort_type)

            _LOGGER.debug("Fetching resort data from: %s", url)
            async with session.get(url, allow_redirects=True) as response:
                response.raise_for_status()
                html = await response.text()

            parsed_data = {}
            if resort_type == TYPE_CROSS_COUNTRY:
                parsed_data.update(
                    await hass.async_add_executor_job(
                        parse_cross_country_resort_page, html, lang
                    )
                )

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
                                overview_data = await hass.async_add_executor_job(
                                    parse_cross_country_overview_data,
                                    overview_html,
                                    lang,
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
                                            resort_name_clean = resort_name_clean.split(
                                                "/"
                                            )[0].strip()

                                        for key, data in overview_data.items():
                                            overview_name = data.get("name", "")
                                            if (
                                                overview_name
                                                and resort_name_clean in overview_name
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

            parsed_data = await hass.async_add_executor_job(
                parse_resort_page, html, area_path, lang
            )

            # Fetch main resort page if price or season is missing and we are on a known subpage
            # e.g. /meribel/schneebericht/ -> /meribel/
            if area_path in _SEASON_PANEL_CACHE:
                parsed_data.update(_SEASON_PANEL_CACHE[area_path])

            if "price" not in parsed_data or area_path not in _SEASON_PANEL_CACHE:
                parts = area_path.strip("/").split("/")
                # List of typical subpages that usually don't have the primary price block
                subpages = [
                    "schneebericht",
                    "wetter",
                    "webcams",
                    "pistenplan",
                    "unterkunft",
                    "bewertungen",
                ]
                if len(parts) > 1 and parts[-1].lower() in subpages:
                    main_path = "/" + "/".join(parts[:-1]) + "/"
                    if main_path != area_path:
                        main_url = urljoin(domain, main_path)
                        _LOGGER.debug(
                            "Price missing on subpage, trying to fetch from main page: %s",
                            main_url,
                        )
                        try:
                            async with session.get(
                                main_url, allow_redirects=True
                            ) as response:
                                if response.status == 200:
                                    main_html = await response.text()
                                    main_data = await hass.async_add_executor_job(
                                        parse_resort_page,
                                        main_html,
                                        main_path,
                                        lang,
                                    )
                                    for key in [
                                        "price",
                                        "operating_hours_start",
                                        "operating_hours_end",
                                        "operation_status",
                                        *_SEASON_PANEL_KEYS,
                                    ]:
                                        if key in main_data and key not in parsed_data:
                                            parsed_data[key] = main_data[key]
                                            _LOGGER.debug(
                                                "Found %s on main page: %s",
                                                key,
                                                parsed_data[key],
                                            )

                                    panel = {
                                        k: main_data[k]
                                        for k in _SEASON_PANEL_KEYS
                                        if k in main_data
                                    }
                                    # Store even when empty: a resort that
                                    # publishes no panel must not be re-fetched
                                    # on every single poll.
                                    _SEASON_PANEL_CACHE[area_path] = panel

                        except Exception as err:
                            _LOGGER.debug(
                                "Could not fetch main page for price: %s", err
                            )

            # Season and opening hours only arrive here and can flip the verdict, so
            # judge again on the merged data - outside the fallback branch, which a
            # cache hit skips entirely.
            evaluate_status(parsed_data)

            # Fetch "New Snow" from region overview (more accurate than detail page)
            region_path_from_data = parsed_data.get("region_path", "").strip("/")
            if region_path_from_data:
                # Built outside the try: the handlers below name it, and an
                # unbound one would turn a fetch failure into a NameError.
                snow_report_url = urljoin(
                    domain, f"/{region_path_from_data}/schneebericht/"
                )
                try:
                    _LOGGER.debug(
                        "Fetching region snow report from: %s", snow_report_url
                    )
                    async with session.get(
                        snow_report_url, allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            overview_html = await response.text()
                            overview_data = await hass.async_add_executor_job(
                                parse_overview_data, overview_html, lang
                            )
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
                            # Naming the url matters: this is a region page,
                            # not the resort's, so the entry the warning is
                            # logged against does not identify what failed.
                            _LOGGER.warning(
                                "Could not fetch region snow report %s: %s",
                                snow_report_url,
                                response.status,
                            )
                except Exception as err:
                    _LOGGER.warning(
                        "Error fetching region snow report %s: %s",
                        snow_report_url,
                        err,
                    )

            # Send data to Webhook
            if webhook_url:
                try:
                    # copy parsed_data and remove keys that are not string
                    json_data = {
                        k: v for k, v in parsed_data.items() if k not in ("last_update")
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

            # Fetch snow forecast images (pages 0-5). These pages belong
            # to the region, not the resort, so every resort in a region
            # asks for the same six urls - hence the shared cache.
            region_path_from_data = parsed_data.get("region_path", "").strip("/")
            if not region_path_from_data:
                _LOGGER.warning(
                    "Region path not found for %s, cannot fetch forecast images.",
                    area_path,
                )
            else:
                for i in range(6):
                    forecast_url = urljoin(
                        domain,
                        f"/{region_path_from_data}/wetter/schneevorhersage/{i}/",
                    )
                    try:
                        image_data = await _async_forecast_images(
                            hass, session, forecast_url, i
                        )
                        if image_data is None:
                            continue

                        # Flatten data into parsed_data
                        if "daily_forecast_url" in image_data:
                            parsed_data[f"forecast_image_day_{i}_url"] = image_data[
                                "daily_forecast_url"
                            ]
                            parsed_data[f"forecast_image_day_{i}_caption"] = (
                                image_data.get("daily_caption", "")
                            )

                        if "summary_url" in image_data:
                            hours = (i + 1) * 24
                            parsed_data[f"summary_image_{hours}h_url"] = image_data[
                                "summary_url"
                            ]
                            parsed_data[f"summary_image_{hours}h_caption"] = (
                                image_data.get("summary_caption", "")
                            )
                    except Exception as err:
                        # Same reason as above, plus these six urls are
                        # shared by every resort of a region - so the resort
                        # in the log line is whichever one asked first.
                        _LOGGER.warning(
                            "Error fetching forecast page %d (%s): %s",
                            i,
                            forecast_url,
                            err,
                        )

            _LOGGER.debug("Parsed resort data for %s: %s", area_path, parsed_data)
            return {area_path: parsed_data}
        except Exception as err:
            # No error log here: the coordinator logs the UpdateFailed itself,
            # once, and then stays quiet while the failure persists. Logging
            # it again would print the same failure twice on every poll.
            _LOGGER.debug(
                "Error fetching or parsing resort data for %s: %s",
                area_path,
                err,
            )
            raise UpdateFailed(f"Error communicating with Bergfex: {err}") from err
