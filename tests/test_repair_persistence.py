"""Repair issues have to still be there after a restart.

An issue that is not persistent is written to the store as a name and a
timestamp and nothing else, and comes back inactive - which the user sees as the
repair having quietly resolved itself. Both of this integration's issues ask the
user to do something that a restart does not do for them, so both have to
survive one.
"""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry, flush_store

from custom_components.bergfex.__init__ import (
    CARD_FILENAME,
    CARD_URL_BASE,
    DUPLICATE_ENTRY_ISSUE_ID,
    LEGACY_CARD_ISSUE_ID,
    _async_backfill_unique_id,
    _async_reconcile_card_resource,
)
from custom_components.bergfex.const import DOMAIN
from tests.test_card_resources import FakeResources

NEW_URL = f"{CARD_URL_BASE}/{CARD_FILENAME}?v=3.0.0"


async def _restart_issue_registry(hass: HomeAssistant) -> ir.IssueRegistry:
    """Write the issue registry out and read it back, as a restart would."""
    registry = ir.async_get(hass)
    await flush_store(registry._store)

    reloaded = ir.IssueRegistry(hass)
    await reloaded.async_load()
    return reloaded


@pytest.mark.asyncio
async def test_legacy_card_issue_survives_a_restart(hass: HomeAssistant):
    """Raised during setup, so a non-persistent one is inactive before it is seen.

    It used to be raised only on the run that removed the stale HACS resource,
    which is why it had to survive a restart on its own - and why it could then
    never be cleared. It is re-evaluated against www/community on every start
    now, so what keeps it visible and what takes it away are separate concerns;
    this test covers the first. See tests/test_standalone_card_issue.py for the
    second.
    """
    resources = FakeResources(
        [
            {
                "id": "hacs",
                "res_type": "module",
                "url": "/hacsfiles/lovelace-bergfex-card/bergfex-card.js",
            }
        ]
    )
    removed = await _async_reconcile_card_resource(resources, NEW_URL)
    assert any("lovelace-bergfex-card" in url for url in removed)

    ir.async_create_issue(
        hass,
        DOMAIN,
        LEGACY_CARD_ISSUE_ID,
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=LEGACY_CARD_ISSUE_ID,
    )

    reloaded = await _restart_issue_registry(hass)
    issue = reloaded.async_get_issue(DOMAIN, LEGACY_CARD_ISSUE_ID)

    assert issue is not None
    assert issue.active is True
    assert issue.translation_key == LEGACY_CARD_ISSUE_ID


@pytest.mark.asyncio
async def test_duplicate_issue_keeps_its_entry_id_across_a_restart(
    hass: HomeAssistant,
):
    """The fix flow deletes the entry named in `data`, so `data` has to survive.

    Setup raises this issue again, but only once the entry is up, and a
    non-persistent issue is stored without its `data` at all - which is why the
    fix flow had to keep a fallback that digs the entry id back out of the issue
    id.
    """
    first = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={
            "name": "Test Resort",
            "country": "Österreich",
            "ski_area": "/test/schneebericht/",
            "language": "at",
            "type": "alpine",
        },
        source="user",
        entry_id="first_entry",
    )
    first.add_to_hass(hass)
    second = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title=first.title,
        data=dict(first.data),
        source="user",
        entry_id="second_entry",
    )
    second.add_to_hass(hass)

    _async_backfill_unique_id(hass, first)
    _async_backfill_unique_id(hass, second)

    issue_id = f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry"
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None

    reloaded = await _restart_issue_registry(hass)
    issue = reloaded.async_get_issue(DOMAIN, issue_id)

    assert issue is not None
    assert issue.active is True
    assert issue.is_fixable is True
    assert issue.data == {"entry_id": "second_entry"}
