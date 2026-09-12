from __future__ import annotations

import logging
import time
from pathlib import Path
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
from homeassistant.helpers import device_registry as dr
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
from .config_flow import entry_area_name
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

# Entries whose setup failure has already been reported at WARNING. Setup is
# retried for as long as the outage lasts, and the reason does not change
# between retries, so the second attempt onwards stays at DEBUG.
_SETUP_FAILURE_LOGGED: set[str] = set()

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
ORPHANED_ENTITIES_ISSUE_ID = "orphaned_registry_entries"

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


def _standalone_card_files(config_dir: str) -> list[str]:
    """Return the standalone card's HACS files that are still on disk.

    HACS unpacks a frontend plugin into www/community/<repository>/, and those
    files outlive the Lovelace resource that pointed at them - removing the
    resource is not uninstalling the repository, which is the whole reason the
    repair exists. Matched on the filename rather than the directory, because
    the repository has been renamed once and both spellings are in the wild.
    """
    community = Path(config_dir) / "www" / "community"
    try:
        return sorted(str(path) for path in community.glob(f"*/{CARD_FILENAME}"))
    except OSError:
        # An unreadable or missing www/ is not evidence of an installation.
        return []


async def _async_report_standalone_card(hass: HomeAssistant) -> None:
    """Raise the "uninstall the HACS card" repair for exactly as long as it is true.

    This used to be raised on the single run that removed the stale Lovelace
    resource, and never re-evaluated. Persistent, so it survived a restart - and
    since no code path deleted it, a user who did precisely what it asked kept
    the warning for good. Asking the filesystem on every start means the repair
    tracks the thing it actually describes, and clears itself the moment HACS
    stops shipping a second copy.
    """
    leftovers = await hass.async_add_executor_job(
        _standalone_card_files, hass.config.config_dir
    )

    if not leftovers:
        ir.async_delete_issue(hass, DOMAIN, LEGACY_CARD_ISSUE_ID)
        return

    _LOGGER.debug("Standalone card still installed by HACS: %s", ", ".join(leftovers))
    ir.async_create_issue(
        hass,
        DOMAIN,
        LEGACY_CARD_ISSUE_ID,
        is_fixable=False,
        # Re-raised every start for as long as the files are there, so it does
        # not need to survive a restart on its own - but a non-persistent issue
        # comes back inactive, and this one is raised during setup, before the
        # user is looking. Persistent keeps it visible; the delete above is what
        # now takes it away.
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=LEGACY_CARD_ISSUE_ID,
    )


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
        # First, and outside every early return below: whether HACS still ships
        # a second copy has nothing to do with how Lovelace stores its
        # resources, and the repair has to be able to clear itself even on an
        # instance this function cannot reconcile.
        await _async_report_standalone_card(hass)

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

        await _async_reconcile_card_resource(resources, new_url)

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
def _async_backfill_unique_id(
    hass: HomeAssistant, entry: ConfigEntry, *, ignore_entry_id: str | None = None
) -> None:
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

    # `ignore_entry_id` is the entry that is being removed right now. Older Home
    # Assistant versions drop it from the registry only after async_remove_entry
    # has returned, so without this it is still listed, still holding the id it
    # is about to give up - and the lookup below would see a collision that no
    # longer exists.
    ignored = {entry.entry_id, ignore_entry_id}

    # No await between the lookup and the update, so no second entry can claim
    # the id in between.
    taken_by = next(
        (
            other
            for other in hass.config_entries.async_entries(DOMAIN)
            if other.entry_id not in ignored and other.unique_id == unique_id
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
    legacy_prefixes = legacy_unique_id_prefixes(entry_area_name(entry))
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


@callback
def _async_orphaned_registry_entries(
    hass: HomeAssistant, entry: ConfigEntry
) -> list[er.RegistryEntry]:
    """Registry rows for this entry that no entity can claim any more.

    The integration has keyed its entities three ways over its life, and
    `_async_migrate_unique_ids` deliberately declines to re-key a row whose new
    id is already taken - two rows cannot share one unique id. Where an install
    carries rows from more than one scheme the superseded ones stay on the
    device with nothing behind them: Home Assistant restores them as
    `unavailable` forever, and the card used to render them as duplicate,
    never-loading forecast images.

    Everything the integration registers today starts with the path-based
    prefix, so a row that does not is a leftover no code path can revive.
    """
    prefix = unique_id_prefix(entry.data[CONF_SKI_AREA])
    registry = er.async_get(hass)
    return [
        row
        for row in er.async_entries_for_config_entry(registry, entry.entry_id)
        if not row.unique_id.startswith(prefix)
    ]


@callback
def _async_report_orphaned_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Offer to delete the leftovers, without ever deleting them unasked.

    Removing registry rows is destructive - the user may have renamed them,
    referenced them from a dashboard or an automation, or be keeping their
    recorder history - so this raises a repair the user can read and dismiss.
    Nothing is removed until they confirm the fix flow.
    """
    issue_id = f"{ORPHANED_ENTITIES_ISSUE_ID}_{entry.entry_id}"
    orphans = _async_orphaned_registry_entries(hass, entry)

    if not orphans:
        # Also covers the run right after the fix flow cleared them.
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    _LOGGER.debug(
        "%s carries %s registry rows from a superseded unique id scheme",
        entry.title,
        len(orphans),
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        data={"entry_id": entry.entry_id},
        # Setup re-raises this every start, but `data` is dropped for a
        # non-persistent issue and the fix flow needs the entry id.
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ORPHANED_ENTITIES_ISSUE_ID,
        translation_placeholders={
            "resort": entry.title,
            "count": str(len(orphans)),
        },
    )


@callback
def _async_refresh_device_name(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Give the device the resort name once the parser has resolved it.

    `device_info` is read when an entity is first registered, and at that moment
    the only name available is the one the config flow stored - which for an
    entry created while name parsing was broken is the URL slug ("achensee").
    The entities correct themselves on every coordinator update, the device does
    not, so the card kept heading those resorts in lower case forever.

    `name_by_user` is left alone by `async_update_device`, so a device the user
    has renamed keeps their name.
    """
    coordinator = hass.data[DOMAIN][COORDINATORS].get(
        coordinator_key(entry.data[CONF_SKI_AREA])
    )
    area_path = entry.data[CONF_SKI_AREA]
    if not coordinator or not coordinator.data:
        return

    resort_name = (coordinator.data.get(area_path) or {}).get("resort_name")
    if not resort_name:
        return

    device_registry = dr.async_get(hass)
    # Looked up within this entry rather than by identifier alone. Identifiers
    # are not unique across config entries, which is why the registry-wide
    # lookup is deprecated - and this resort's device is this entry's device.
    device = next(
        (
            candidate
            for candidate in dr.async_entries_for_config_entry(
                device_registry, entry.entry_id
            )
            if (DOMAIN, area_path) in candidate.identifiers
        ),
        None,
    )
    if device is None or device.name == resort_name:
        return

    _LOGGER.debug(
        "Renaming device %s to the parsed resort name %s", device.name, resort_name
    )
    device_registry.async_update_device(device.id, name=resort_name)


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
    area_name = entry_area_name(entry)
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

        update_interval_minutes = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
            name=resort_coordinator_name,
            update_method=async_update_data_resort,
            update_interval=timedelta(minutes=update_interval_minutes),
        )
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            # Nothing else says why this failed. Home Assistant's own
            # "not ready yet" line is INFO, which the default WARNING level
            # hides, and `async_config_entry_first_refresh` asks the
            # coordinator not to log the failure at all. So the reason has to
            # travel in the exception - that is what the entry page shows the
            # user - and one line has to reach the log.
            #
            # Only the first attempt is worth a warning: setup is retried on a
            # backoff for as long as the outage lasts, and a warning per retry
            # is the noise this whole path was cleaned up to remove.
            if entry.entry_id in _SETUP_FAILURE_LOGGED:
                _LOGGER.debug(
                    "Still failing to refresh resort coordinator for %s: %s",
                    area_name,
                    err,
                )
            else:
                _SETUP_FAILURE_LOGGED.add(entry.entry_id)
                _LOGGER.warning(
                    "Failed to refresh resort coordinator for %s: %s", area_name, err
                )
            raise ConfigEntryNotReady(
                f"Error communicating with Bergfex for {area_name}: {err}"
            ) from err

        hass.data[DOMAIN][COORDINATORS][resort_coordinator_name] = coordinator

    # `entry.runtime_data` is a non-public attribute. Coordinator is stored
    # in `hass.data[DOMAIN][COORDINATORS]` and should be retrieved from there
    # by platforms during setup. Do not set `entry.runtime_data`.

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Both need the platforms to have run: the device does not exist until an
    # entity registers it, and a row is only a leftover once the entities that
    # could still claim it have been added.
    _async_refresh_device_name(hass, entry)
    _async_report_orphaned_entities(hass, entry)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Setup got through, so the next outage deserves its warning again.
    _SETUP_FAILURE_LOGGED.discard(entry.entry_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _SETUP_FAILURE_LOGGED.discard(entry.entry_id)
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
    resort's unique id. Hand it to the leftover here rather than leaving it
    unidentifiable, and its repair issue raised, until the next restart.

    Whether the removed entry is still listed at this point depends on the Home
    Assistant version: 2025.1 drops it from the registry only after this callback
    returns, later versions before. So the handover names it explicitly rather
    than trusting it to be gone.
    """
    ir.async_delete_issue(hass, DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_{entry.entry_id}")
    # Removing the entry takes its registry rows with it, leftovers included, so
    # the orphan repair has nothing left to fix either.
    ir.async_delete_issue(
        hass, DOMAIN, f"{ORPHANED_ENTITIES_ISSUE_ID}_{entry.entry_id}"
    )

    ski_area = entry.data.get(CONF_SKI_AREA)
    if ski_area is None:
        return

    for other in hass.config_entries.async_entries(DOMAIN):
        if other.entry_id == entry.entry_id:
            continue
        if other.unique_id is None and other.data.get(CONF_SKI_AREA) == ski_area:
            # Backfilling re-runs the same first-come rule, so with three entries
            # for one resort the remaining leftover keeps its issue.
            _async_backfill_unique_id(hass, other, ignore_entry_id=entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow deleting a device the entry no longer provides.

    Without this hook Home Assistant hides the delete button altogether, so a
    device left behind by an earlier version - or by a resort whose bergfex path
    changed - sits greyed out with its entities forever and the only way out is
    removing the whole entry.

    An entry serves exactly one resort, so the device that matches the entry's
    current ski area is still live and must stay: deleting it would only have
    Home Assistant recreate it on the next poll, minus the user's area, name and
    dashboard references. Everything else under this entry is stale.
    """
    area_path = entry.data.get(CONF_SKI_AREA)
    if area_path is None:
        # With nothing to compare against, every identifier - the live device's
        # included - would come out unequal and the whole entry would go
        # deletable. Refusing is the safe answer: the user can still remove the
        # entry itself.
        _LOGGER.debug(
            "Entry %s carries no ski area; refusing device deletion", entry.entry_id
        )
        return False

    return not any(
        domain == DOMAIN and identifier == area_path
        for domain, identifier in device.identifiers
    )


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
