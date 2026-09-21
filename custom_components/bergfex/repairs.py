"""Repair flows for Bergfex."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from . import (
    DUPLICATE_ENTRY_ISSUE_ID,
    ORPHANED_ENTITIES_ISSUE_ID,
    _async_orphaned_registry_entries,
)
from homeassistant.helpers import entity_registry as er
from .const import CONF_SKI_AREA


class DuplicateEntryRepairFlow(RepairsFlow):
    """Delete the duplicate config entry the issue was raised for.

    Both entries for a resort carry the same title, so asking the user to pick
    the right row in Settings > Devices & Services is asking them to guess. The
    issue knows which entry it is about, so let it do the deleting.
    """

    def __init__(self, entry_id: str) -> None:
        """Remember which entry this issue is about."""
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Start the fix flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Confirm, then remove the duplicate entry."""
        entry = self.hass.config_entries.async_get_entry(self._entry_id)

        if entry is None:
            # Already deleted by hand. Finishing clears the issue, which is all
            # that is left to do.
            return self.async_create_entry(data={})

        if user_input is not None:
            # Removing the entry runs async_remove_entry, which drops this issue
            # and hands the resort's unique id to whichever entry is left.
            await self.hass.config_entries.async_remove(self._entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "resort": entry.title,
                "path": entry.data.get(CONF_SKI_AREA, ""),
                "entry_id": entry.entry_id,
            },
        )


class OrphanedEntitiesRepairFlow(RepairsFlow):
    """Delete the registry rows a superseded unique id scheme left behind.

    A repair rather than something setup does on its own: the rows carry the
    user's renames, areas and recorder history, so the destructive half is opt-in.
    The card ignores the rows in the meantime.
    """

    def __init__(self, entry_id: str) -> None:
        """Remember which entry this issue is about."""
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Start the fix flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Confirm, then remove the leftover rows."""
        entry = self.hass.config_entries.async_get_entry(self._entry_id)

        if entry is None:
            # The entry went away, and its registry rows with it.
            return self.async_create_entry(data={})

        orphans = _async_orphaned_registry_entries(self.hass, entry)

        if user_input is not None:
            registry = er.async_get(self.hass)
            for row in orphans:
                registry.async_remove(row.entity_id)
            return self.async_create_entry(data={})

        # Recomputed rather than read from the issue, so the list the user
        # confirms is the list that gets deleted even if a restart changed it.
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "resort": entry.title,
                "count": str(len(orphans)),
                "entities": "\n".join(f"- {row.entity_id}" for row in orphans),
            },
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Build the fix flow for a repair issue."""
    entry_id = ""
    if data:
        entry_id = str(data.get("entry_id") or "")

    if issue_id.startswith(f"{ORPHANED_ENTITIES_ISSUE_ID}_"):
        if not entry_id:
            entry_id = issue_id[len(ORPHANED_ENTITIES_ISSUE_ID) + 1 :]
        return OrphanedEntitiesRepairFlow(entry_id)

    if not entry_id and issue_id.startswith(f"{DUPLICATE_ENTRY_ISSUE_ID}_"):
        # Issues raised before the id was carried in `data` are keyed on it.
        entry_id = issue_id[len(DUPLICATE_ENTRY_ISSUE_ID) + 1 :]

    return DuplicateEntryRepairFlow(entry_id)
