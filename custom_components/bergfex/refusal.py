"""Counting refusals, and saying so once they stop looking like a hiccup.

Home Assistant builds a fresh coordinator on every setup retry, so a counter on
the coordinator resets every five, ten, twenty seconds and never reaches any
threshold - which is exactly the case this exists for, an entry that never
finishes setting up. The count therefore lives here, in module state keyed on
the entry id, mirroring _SETUP_FAILURE_LOGGED in __init__.py, which solves the
same problem for the same reason.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .fetch import BergfexRefused

_LOGGER = logging.getLogger(__name__)

REQUESTS_REFUSED_ISSUE_ID = "requests_refused"

# Home Assistant retries a failed setup at 5, 10, 20, 40, 80 seconds, so the
# fifth refusal lands about two and a half minutes after the first. That rides
# out a restart, a router still negotiating at boot, and a short maintenance
# window, while still showing up within the first look at the instance. On an
# entry that is already running, the same five are five polls - two and a half
# hours at the default interval, which is a fair bar for "not transient".
REFUSAL_THRESHOLD = 5


@dataclass
class _EntryRefusal:
    """What one entry's run of refusals has told us so far."""

    host: str
    status: int
    consecutive: int = 0
    cf_ray: str | None = None
    requested_url: str = ""
    final_url: str = ""
    excerpt: str = ""
    first_seen: str = ""
    last_seen: str = ""
    extra: dict = field(default_factory=dict)


_STATE: dict[str, _EntryRefusal] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _entry_titles(hass: HomeAssistant, host: str) -> str:
    """Name the resorts a host is refusing, in the order Home Assistant lists them."""
    titles = [
        entry.title
        for entry in hass.config_entries.async_entries(DOMAIN)
        if (state := _STATE.get(entry.entry_id)) is not None and state.host == host
    ]
    return ", ".join(titles)


def _hosts_over_threshold() -> set[str]:
    return {
        state.host
        for state in _STATE.values()
        if state.consecutive >= REFUSAL_THRESHOLD
    }


@callback
def _async_sync_issue(hass: HomeAssistant, host: str) -> None:
    """Raise or drop the issue for one host, from whatever the state now says."""
    issue_id = f"{REQUESTS_REFUSED_ISSUE_ID}_{host}"

    if host not in _hosts_over_threshold():
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    worst = max(
        (state for state in _STATE.values() if state.host == host),
        key=lambda state: state.consecutive,
    )

    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        # Raised during setup, before the user is looking - the same reasoning
        # the standalone-card issue carries. The delete above is what takes it
        # away.
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key=REQUESTS_REFUSED_ISSUE_ID,
        translation_placeholders={
            "host": host,
            "status": str(worst.status),
            "resorts": _entry_titles(hass, host) or host,
            "cf_ray": worst.cf_ray or "-",
        },
    )


@callback
def async_note_refusal(
    hass: HomeAssistant, entry: ConfigEntry, err: BergfexRefused
) -> None:
    """Record one refusal, and raise the issue once a host has had enough of them.

    Only a refusal counts. A 404 means the path is wrong and a 500 means bergfex
    is having a bad day; neither is the network turning us away, and saying so
    would send the user after the wrong thing.
    """
    if not err.is_refusal:
        return

    previous = _STATE.get(entry.entry_id)
    consecutive = previous.consecutive + 1 if previous else 1

    _STATE[entry.entry_id] = _EntryRefusal(
        host=err.host,
        status=err.status,
        consecutive=consecutive,
        cf_ray=err.cf_ray,
        requested_url=err.requested_url,
        final_url=err.final_url,
        excerpt=err.excerpt,
        first_seen=previous.first_seen if previous else _now(),
        last_seen=_now(),
    )

    _async_sync_issue(hass, err.host)


@callback
def async_note_success(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Forget this entry's run. One page through proves the network is not blocked."""
    state = _STATE.pop(entry.entry_id, None)
    if state is not None:
        _async_sync_issue(hass, state.host)


@callback
def async_drop_stale_issues(hass: HomeAssistant) -> None:
    """Drop refused-host repairs that nothing in this run stands behind.

    The repair is persistent so that it survives the restart it is usually raised
    right after, but the count behind it lives in _STATE, which a restart empties.
    A repair carried over from before then has no owner: only an entry polling
    that host can clear it, and once every entry has moved to another host - the
    way out the repair itself suggests - none ever will. Dropping it at setup is
    safe because it is rebuilt from fresh evidence: a host that still refuses
    raises it again after REFUSAL_THRESHOLD polls.
    """
    prefix = f"{REQUESTS_REFUSED_ISSUE_ID}_"
    backed = {state.host for state in _STATE.values()}
    stale = [
        issue_id
        for domain, issue_id in ir.async_get(hass).issues
        if domain == DOMAIN
        and issue_id.startswith(prefix)
        and issue_id.removeprefix(prefix) not in backed
    ]
    for issue_id in stale:
        _LOGGER.debug("Dropping %s, left over from before this start", issue_id)
        ir.async_delete_issue(hass, DOMAIN, issue_id)


@callback
def async_forget_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop a removed entry, and the issue with it if it was the last one."""
    async_note_success(hass, entry)


def refusal_snapshot() -> dict[str, dict]:
    """Return what is known about the current refusals, for diagnostics.

    This is the channel that matters: an entry that never finished setting up
    has no coordinator and therefore no last_exception in the download, which is
    precisely the entry a report is attached to.
    """
    return {
        entry_id: {
            "host": state.host,
            "status": state.status,
            "consecutive": state.consecutive,
            "cf_ray": state.cf_ray,
            "requested_url": state.requested_url,
            "final_url": state.final_url,
            "excerpt": state.excerpt,
            "first_seen": state.first_seen,
            "last_seen": state.last_seen,
        }
        for entry_id, state in _STATE.items()
    }
