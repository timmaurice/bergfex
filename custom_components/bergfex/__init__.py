from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady


import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_SKI_AREA,
    DOMAIN,
)
from .config_flow import entry_area_name

# BergfexConfigEntry lives with the coordinator it types. It stays importable
# from the package, where the platforms and other modules look for it.
from .coordinator import BergfexConfigEntry, BergfexCoordinator
from .unique_id import (
    legacy_unique_id_prefixes,
    unique_id_prefix,
)

PLATFORMS = ["sensor", "image"]
_LOGGER = logging.getLogger(__name__)

# Entries whose setup failure has already been reported at WARNING. Setup is
# retried for as long as the outage lasts, and the reason does not change
# between retries, so the second attempt onwards stays at DEBUG.
_SETUP_FAILURE_LOGGED: set[str] = set()

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
    # The store loads lazily: until awaited, async_items() is empty, and
    # reconciling off that appends another copy of our resource every restart.
    # Default to False - assuming an unrecognised collection is loaded would
    # save a store that has lost every other card's resource.
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
            # Any other bergfex-card.js is a leftover - the HACS copy, a hand-added
            # /local/ entry - and loads a second bundle that fights ours over the
            # element name.
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

    HACS unpacks a plugin into www/community/<repository>/, and those files
    outlive the Lovelace resource pointing at them. Matched on the filename, not
    the directory: the repository was renamed once and both spellings exist.
    """
    community = Path(config_dir) / "www" / "community"
    try:
        return sorted(str(path) for path in community.glob(f"*/{CARD_FILENAME}"))
    except OSError:
        # An unreadable or missing www/ is not evidence of an installation.
        return []


async def _async_report_standalone_card(hass: HomeAssistant) -> None:
    """Raise the "uninstall the HACS card" repair for exactly as long as it is true.

    Asked of the filesystem on every start, so it tracks what it describes and
    clears itself once HACS stops shipping a second copy.
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
        # Persistent because a non-persistent issue comes back inactive, and this
        # is raised during setup before the user is looking. The delete above is
        # what takes it away.
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=LEGACY_CARD_ISSUE_ID,
    )


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
        # Before every early return below: the repair has to be able to clear
        # itself even on an instance whose resources cannot be reconciled.
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

    Two entries for one resort would get the same unique id, which Home Assistant
    refuses with a collision repair of its own on every restart. So only the first
    gets the id; the leftover keeps unique_id None and is offered as a repair.
    """
    unique_id = entry.data[CONF_SKI_AREA]
    issue_id = f"{DUPLICATE_ENTRY_ISSUE_ID}_{entry.entry_id}"

    # The entry being removed right now. Older Home Assistant versions drop it
    # only after async_remove_entry returns, so the lookup below would see a
    # collision that no longer exists.
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
    # Both entries carry the same title, so naming the resort would not tell
    # the user which row to delete. Raised per entry, carrying that entry's id.
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        data={"entry_id": entry.entry_id},
        # Persistent because `data` is dropped for a non-persistent issue, and the
        # fix flow needs the entry id to know which row to delete.
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

    Entities were keyed on the display name, which is not unique, so resorts that
    slugify alike collided. Rewriting the id in place rather than registering the
    new one keeps the registry row, and with it the entity_id, name, area and
    recorder history.
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

        # Two entries for the same resort would migrate onto the same ids and the
        # registry rejects the second, aborting setup. The leftover keeps its old
        # ids until the repair removes it.
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

    Entities have been keyed three ways, and the migration declines to re-key a
    row whose new id is taken, so superseded rows stay on the device restored as
    `unavailable`. Everything registered today carries the path-based prefix, so
    a row that does not is a leftover no code path can revive.
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
def _async_refresh_device_name(hass: HomeAssistant, entry: BergfexConfigEntry) -> None:
    """Give the device the resort name once the parser has resolved it.

    `device_info` is read once, when the first entity registers, and the only name
    available then is the one the config flow stored - a URL slug for entries
    created while name parsing was broken. Entities correct themselves on every
    update; the device does not. `name_by_user` is left alone, so a device the
    user renamed keeps their name.
    """
    coordinator = entry.runtime_data
    area_path = entry.data[CONF_SKI_AREA]
    if not coordinator.data:
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


async def async_setup_entry(hass: HomeAssistant, entry: BergfexConfigEntry) -> bool:
    """Set up Bergfex from a config entry."""
    # Entries created before the config flow set a unique id carry None, so the
    # duplicate check in the flow would not catch a resort that is already
    # installed. The resort path is stable across domains and languages.
    if entry.unique_id is None:
        _async_backfill_unique_id(hass, entry)

    await _async_migrate_unique_ids(hass, entry)

    area_name = entry_area_name(entry)

    _LOGGER.debug("Creating resort coordinator for %s to fetch detail page", area_name)
    coordinator = BergfexCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        # Nothing else says why this failed: Home Assistant's own line is INFO,
        # which the default level hides, and the coordinator is asked not to log
        # it at all. Only the first attempt warns - setup retries on a backoff for
        # as long as the outage lasts.
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

    # Only a coordinator that got through its first refresh is kept. Home
    # Assistant drops runtime_data again when the entry unloads.
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Both need the platforms to have run: the device does not exist until an
    # entity registers it, and a row is only a leftover once the entities that
    # could still claim it have been added.
    _async_refresh_device_name(hass, entry)
    _async_report_orphaned_entities(hass, entry)

    # No update listener: the options flow reloads the entry itself
    # (OptionsFlowWithReload), and so does the reconfigure step. A listener on
    # top would reload a second time, and core reports the combination.

    # Setup got through, so the next outage deserves its warning again.
    _SETUP_FAILURE_LOGGED.discard(entry.entry_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BergfexConfigEntry) -> bool:
    """Unload a config entry."""
    _SETUP_FAILURE_LOGGED.discard(entry.entry_id)
    # Forward the unloading to the sensor and image platforms. The coordinator
    # lives in runtime_data, which goes with the entry, so nothing is left to pop.
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up after a removed entry.

    The repair issue is keyed on the removed entry, so nothing else would clear
    it. If the entry that won the resort's unique id is the one removed, hand the
    id to the leftover here rather than leaving it unidentifiable until restart.

    Whether the removed entry is still listed depends on the Home Assistant
    version, so the handover names it explicitly.
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

    Without this hook the delete button is hidden, so a device left behind by an
    earlier version sits greyed out forever. An entry serves one resort, so the
    device matching its current ski area is live and must stay - deleting it would
    only have it recreated minus the user's area, name and dashboard references.
    """
    area_path = entry.data.get(CONF_SKI_AREA)
    if area_path is None:
        # With nothing to compare against, every identifier would come out unequal
        # and the whole entry would go deletable. The user can still remove the
        # entry itself.
        _LOGGER.debug(
            "Entry %s carries no ski area; refusing device deletion", entry.entry_id
        )
        return False

    return not any(
        domain == DOMAIN and identifier == area_path
        for domain, identifier in device.identifiers
    )
