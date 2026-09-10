from __future__ import annotations

import logging
import time
from typing import Any
from datetime import timedelta, datetime
from urllib.parse import urljoin, urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady


import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

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
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .unique_id import (
    coordinator_key,
    legacy_unique_id_prefixes,
    unique_id_prefix,
)
from .parser import (
    evaluate_status,
    parse_cross_country_resort_page,
    parse_cross_country_overview_data,
    parse_overview_data,
    parse_resort_page,
    parse_snow_forecast_images,
)

PLATFORMS = ["sensor", "image"]
_LOGGER = logging.getLogger(__name__)

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

# A region's snow-forecast pages are the same pages for every resort in it, so
# with several resorts from one region installed the integration was fetching
# and re-parsing the identical six pages once per resort per poll. They are keyed
# on the url and shared across coordinators.
#
# The TTL is generous on purpose: these are bergfex's own forecast graphics,
# republished a few times a day, so a resort that joins the cycle a few minutes
# late loses nothing by reading the parse the previous one just did. It is well
# under MIN_UPDATE_INTERVAL's own reach, so a region is still refetched regularly.
_FORECAST_CACHE: dict[str, tuple[float, dict[str, str]]] = {}
_FORECAST_CACHE_TTL = 10 * 60

CARD_FILENAME = "bergfex-card.js"
CARD_URL_BASE = "/bergfex_frontend"

LEGACY_CARD_ISSUE_ID = "standalone_card_installed"
DUPLICATE_ENTRY_ISSUE_ID = "duplicate_resort_entry"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _is_bergfex_card_resource(url: str) -> bool:
    """Return True for any Lovelace resource that loads a Bergfex card bundle.

    Matches the bundle we serve as well as leftovers from the standalone
    lovelace-bergfex-card, wherever the user happened to put them.
    """
    return urlparse(url).path.rsplit("/", 1)[-1] == CARD_FILENAME


async def _async_reconcile_card_resource(resources, new_url: str) -> list[str]:
    """Leave exactly one Lovelace resource pointing at the bundled card.

    Returns the URLs of the resources that were removed.
    """
    # The resource store is loaded lazily: until something awaits it,
    # async_items() returns an empty list. Reconciling off that empty list
    # appended another copy of our resource on every restart.
    #
    # Default to False, not True: assuming a collection we cannot recognise is
    # already loaded would let us reconcile against an empty item list and save
    # a store that has lost every other card's resource. Missing async_load
    # raises instead, and the caller skips registration.
    if not getattr(resources, "loaded", False):
        await resources.async_load()
        resources.loaded = True

    # Collect first, mutate after: async_items() must not change while iterating.
    own_resource = None
    stale_resources = []

    for item in resources.async_items():
        url = item.get("url", "")
        if not _is_bergfex_card_resource(url):
            continue
        if url.startswith(f"{CARD_URL_BASE}/") and own_resource is None:
            own_resource = item
        else:
            # Anything else pointing at a bergfex-card.js is a leftover: the
            # HACS copy, a hand-added /local/ entry, or a duplicate of ours.
            # Leaving it in place loads a second bundle that fights ours over
            # the bergfex-card element name.
            stale_resources.append(item)

    for item in stale_resources:
        _LOGGER.info(
            "Removing stale Bergfex card resource %s; the card now ships with the integration",
            item.get("url"),
        )
        await resources.async_delete_item(item.get("id"))

    if own_resource is None:
        await resources.async_create_item({"res_type": "module", "url": new_url})
    elif own_resource.get("url") != new_url:
        await resources.async_update_item(own_resource.get("id"), {"url": new_url})

    return [item.get("url", "") for item in stale_resources]


async def _async_forecast_images(
    hass: HomeAssistant, session, forecast_url: str, page: int
) -> dict[str, str] | None:
    """Return one region forecast page's images, fetching it at most once per TTL.

    Snow forecast pages are per region. With several resorts of one region
    installed, every poll used to fetch and re-parse the identical six pages once
    per resort, so the work grew with the number of resorts rather than with the
    number of regions.

    Returns None when the page could not be read, which the caller skips.
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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Bergfex component and register the Lovelace card."""
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.loader import async_get_integration

    integration = await async_get_integration(hass, DOMAIN)
    version = integration.version or "1.0.0"

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=f"{CARD_URL_BASE}/{CARD_FILENAME}",
                path=hass.config.path(f"custom_components/{DOMAIN}/{CARD_FILENAME}"),
                cache_headers=True,
            )
        ]
    )
    new_url = f"{CARD_URL_BASE}/{CARD_FILENAME}?v={version}"

    async def _async_register_lovelace_resource(event=None):
        if "lovelace" not in hass.data:
            _LOGGER.warning("Lovelace not found in hass.data")
            return

        lovelace_data = hass.data["lovelace"]
        mode = getattr(lovelace_data, "resource_mode", "storage")
        resources = getattr(lovelace_data, "resources", None)

        if not resources:
            _LOGGER.warning("Lovelace data does not have resources")
            return

        if mode != "storage":
            _LOGGER.warning(
                "Lovelace is not in storage mode (mode is '%s'), cannot auto-register",
                mode,
            )
            return

        removed_urls = await _async_reconcile_card_resource(resources, new_url)

        # Dropping the resource does not uninstall the HACS repository: its files
        # stay in www/community and HACS keeps offering updates for them. Ask the
        # user to remove it so the two copies cannot diverge.
        if any("lovelace-bergfex-card" in url for url in removed_urls):
            ir.async_create_issue(
                hass,
                DOMAIN,
                LEGACY_CARD_ISSUE_ID,
                is_fixable=False,
                # Only raised on the run that actually removed the resource, so
                # nothing re-raises it later. A non-persistent issue is reloaded
                # inactive after a restart, which made this one vanish before
                # anyone had acted on it - while the HACS copy it asks about was
                # still installed.
                is_persistent=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=LEGACY_CARD_ISSUE_ID,
            )

    from homeassistant.core import CoreState
    from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

    if hass.state == CoreState.running:
        await _async_register_lovelace_resource()
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, _async_register_lovelace_resource
        )

    return True


@callback
def _async_backfill_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Give a pre-unique-id entry the resort path as its id, if it is still free.

    A user who hit the duplicate bug has two entries for one resort. Backfilling
    both would hand Home Assistant two entries with the same unique id: it
    refuses the second, logs an error asking the user to file a bug against this
    integration, and raises its own collision repair - on every restart, forever.

    So only the first entry gets the id. The leftover keeps unique_id None (it
    still works, it just cannot be recognized as a duplicate) and the user gets a
    repair that names that exact entry and, when they confirm it, deletes it -
    which is the only thing that actually resolves the situation.
    """
    unique_id = entry.data[CONF_SKI_AREA]
    issue_id = f"{DUPLICATE_ENTRY_ISSUE_ID}_{entry.entry_id}"

    # No await between the lookup and the update, so no second entry can claim
    # the id in between.
    taken_by = next(
        (
            other
            for other in hass.config_entries.async_entries(DOMAIN)
            if other.entry_id != entry.entry_id and other.unique_id == unique_id
        ),
        None,
    )

    if taken_by is None:
        hass.config_entries.async_update_entry(entry, unique_id=unique_id)
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    _LOGGER.warning(
        "Config entry %s (%s) duplicates %s (%s); leaving its unique id unset",
        entry.title,
        entry.entry_id,
        taken_by.entry_id,
        unique_id,
    )
    # Both entries carry the same title, so naming the resort does not tell the
    # user which of the two rows to delete. The issue is raised per entry and
    # carries that entry's id, and the repair flow deletes exactly that entry -
    # so the user never has to tell them apart by hand.
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        data={"entry_id": entry.entry_id},
        # Setup re-raises this one, so it does come back - but only once the
        # entry has been set up, and `data` is dropped entirely for a
        # non-persistent issue. The fix flow needs that entry id to know which
        # row to delete.
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=DUPLICATE_ENTRY_ISSUE_ID,
        translation_placeholders={
            "resort": entry.title,
            "path": unique_id,
            "entry_id": entry.entry_id,
        },
    )



async def _async_migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move this entry's entities onto path-based unique ids.

    The entities were keyed on the display name, which is not unique, so two
    resorts whose names slugify alike collided and Home Assistant kept only the
    first resort's entities. Re-keying them onto the resort path fixes that, but
    only a migration makes it safe: registering the new ids bare would leave
    every existing entity behind as an orphan, and with it the user's history,
    their customisations and every dashboard that names them.

    Rewriting the id in place keeps the registry entry - so the entity_id, the
    name, the area and the recorder statistics all stay attached to it.
    """
    new_prefix = unique_id_prefix(entry.data[CONF_SKI_AREA])
    legacy_prefixes = legacy_unique_id_prefixes(entry.data["name"])
    registry = er.async_get(hass)

    @callback
    def _migrate(registry_entry: er.RegistryEntry) -> dict[str, str] | None:
        old_id = registry_entry.unique_id

        legacy_prefix = next(
            (prefix for prefix in legacy_prefixes if old_id.startswith(prefix)), None
        )
        if legacy_prefix is None:
            # Already migrated, which is the normal case from the second restart
            # onwards. Returning None leaves the entry untouched.
            return None

        new_id = f"{new_prefix}{old_id[len(legacy_prefix) :]}"
        if new_id == old_id:
            # A resort whose name and path happen to agree is already correct.
            return None

        # Two entries for the same resort - the duplicate bug the repair issue
        # is about - would both migrate onto the same ids, and the registry
        # rejects the second with a ValueError that would abort setup. The
        # leftover entry keeps its old ids until the repair removes it.
        if registry.async_get_entity_id(
            registry_entry.domain, registry_entry.platform, new_id
        ):
            _LOGGER.debug(
                "Not migrating %s: unique id %s is already taken",
                registry_entry.entity_id,
                new_id,
            )
            return None

        _LOGGER.debug(
            "Migrating %s from unique id %s to %s",
            registry_entry.entity_id,
            old_id,
            new_id,
        )
        return {"new_unique_id": new_id}

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bergfex from a config entry."""
    # Entries created before the config flow set a unique id carry None, so the
    # duplicate check in the flow would not catch a resort that is already
    # installed. The resort path is stable across domains and languages.
    if entry.unique_id is None:
        _async_backfill_unique_id(hass, entry)

    await _async_migrate_unique_ids(hass, entry)

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
    resort_coordinator_name = coordinator_key(area_path)
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
                                    overview_data = (
                                        await hass.async_add_executor_job(
                                            parse_cross_country_overview_data,
                                            overview_html,
                                            lang,
                                        )
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
                                        main_data = (
                                            await hass.async_add_executor_job(
                                                parse_resort_page,
                                                main_html,
                                                main_path,
                                                lang,
                                            )
                                        )
                                        for key in [
                                            "price",
                                            "operating_hours_start",
                                            "operating_hours_end",
                                            "operation_status",
                                            *_SEASON_PANEL_KEYS,
                                        ]:
                                            if (
                                                key in main_data
                                                and key not in parsed_data
                                            ):
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

                # The season and opening hours only arrive here, and they can flip
                # the verdict. Judge it again on the merged data - outside the
                # fallback branch, because a cache hit skips that branch entirely
                # and used to leave the subpage's season-less verdict standing.
                evaluate_status(parsed_data)

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
                                overview_data = (
                                    await hass.async_add_executor_job(
                                        parse_overview_data, overview_html, lang
                                    )
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
                        try:
                            forecast_url = urljoin(
                                domain,
                                f"/{region_path_from_data}/wetter/schneevorhersage/{i}/",
                            )
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
                            _LOGGER.warning(
                                "Error fetching forecast page %d: %s", i, err
                            )

                _LOGGER.debug("Parsed resort data for %s: %s", area_path, parsed_data)
                return {area_path: parsed_data}
            except Exception as err:
                _LOGGER.error(
                    "Error fetching or parsing resort data for %s: %s",
                    area_path,
                    err,
                )
                raise UpdateFailed(f"Error communicating with Bergfex: {err}") from err

        update_interval_minutes = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=resort_coordinator_name,
            update_method=async_update_data_resort,
            update_interval=timedelta(minutes=update_interval_minutes),
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

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Forward the unloading to the sensor platform
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if DOMAIN in hass.data and COORDINATORS in hass.data[DOMAIN]:
            hass.data[DOMAIN][COORDINATORS].pop(
                coordinator_key(entry.data[CONF_SKI_AREA]), None
            )
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up after a removed entry.

    Deleting the leftover duplicate is exactly what the repair issue asks for, so
    the issue has to go with it - nothing else would ever clear it, since it is
    keyed on an entry that no longer exists.

    The user may just as well delete the other one, the entry that won the
    resort's unique id. Home Assistant has already dropped the removed entry from
    the registry by the time this runs, so the id is free right now: hand it to
    the leftover here rather than leaving it unidentifiable, and its repair issue
    raised, until the next restart.
    """
    ir.async_delete_issue(hass, DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_{entry.entry_id}")

    ski_area = entry.data.get(CONF_SKI_AREA)
    if ski_area is None:
        return

    for other in hass.config_entries.async_entries(DOMAIN):
        if other.entry_id == entry.entry_id:
            continue
        if other.unique_id is None and other.data.get(CONF_SKI_AREA) == ski_area:
            # Backfilling re-runs the same first-come rule, so with three entries
            # for one resort the remaining leftover keeps its issue.
            _async_backfill_unique_id(hass, other)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
