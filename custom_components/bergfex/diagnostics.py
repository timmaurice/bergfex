"""Diagnostics support for the Bergfex Snow Report integration."""

from __future__ import annotations

import time
from datetime import date
from typing import Any
from urllib.parse import urljoin

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.core import HomeAssistant

from .const import (
    BASE_URL,
    CONF_DOMAIN,
    CONF_TYPE,
    CONF_WEBHOOK_URL,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)
from .coordinator import (
    _FORECAST_CACHE,
    _FORECAST_CACHE_TTL,
    _SEASON_PANEL_CACHE,
    BergfexConfigEntry,
)

# The webhook url is the only secret an entry holds: whoever has it can post to
# the display it feeds (a TRMNL plugin url is its only credential). Resort,
# country, language and domain are public bergfex coordinates, and a diagnostics
# download ends up attached to a public issue.
TO_REDACT = {CONF_WEBHOOK_URL}

# What decides the state of the resort's sensors, and so what a report about a
# resort that shows wrong or stale data needs to see. The rest of the parsed data
# is named in "keys" but not repeated: the piste list is long, and the forecast
# image urls say nothing a count does not.
_COMMON_KEYS = (
    "resort_name",
    "region_path",
    "status",
    "operation_status",
    "operating_hours_start",
    "operating_hours_end",
    "last_update",
)
_ALPINE_KEYS = (
    "winter_season_start",
    "winter_season_end",
    "summer_season_start",
    "summer_season_end",
    "snow_mountain",
    "snow_valley",
    "new_snow",
    "snow_condition",
    "last_snowfall",
    "avalanche_warning",
    "lifts_open_count",
    "lifts_total_count",
    "slopes_open_count",
    "slopes_total_count",
    "slopes_open_km",
    "slopes_total_km",
    "slope_condition",
    "price",
)
_CROSS_COUNTRY_KEYS = (
    "classical_open_km",
    "classical_total_km",
    "classical_condition",
    "skating_open_km",
    "skating_total_km",
    "skating_condition",
)

# The coordinator asks for pages 0-5 of a region's snow forecast, and flattens
# each page's images into two keys per image on the area.
_FORECAST_PAGES = range(6)
_FORECAST_IMAGE_PREFIXES = ("forecast_image_day_", "summary_image_")


def _plain(value: Any) -> Any:
    """Return a date or datetime as ISO text, anything else unchanged."""
    if isinstance(value, date):
        return value.isoformat()
    return value


def _redact_text(text: str, secrets: list[str]) -> str:
    """Remove the secrets from free text such as an exception message."""
    for secret in secrets:
        text = text.replace(secret, REDACTED)
    return text


def _area_summary(area_data: dict[str, Any], resort_type: str) -> dict[str, Any]:
    """Return what decides an area's sensors, without the bulky parts."""
    type_keys = (
        _CROSS_COUNTRY_KEYS if resort_type == TYPE_CROSS_COUNTRY else _ALPINE_KEYS
    )
    image_keys = [key for key in area_data if key.startswith(_FORECAST_IMAGE_PREFIXES)]
    return {
        # Without the image keys: two per image, and the count below says it.
        "keys": sorted(key for key in area_data if key not in image_keys),
        # None for a field bergfex did not report, so a missing sensor value
        # reads as "not on the page" rather than as a gap in this report.
        **{key: _plain(area_data.get(key)) for key in (*_COMMON_KEYS, *type_keys)},
        "open_pistes_count": len(area_data.get("open_pistes") or []),
        "forecast_image_count": sum(1 for key in image_keys if key.endswith("_url")),
    }


def _forecast_cache_info(
    cache: dict[str, Any], ttl: float | None, domain: str, region_path: str | None
) -> dict[str, Any] | None:
    """Return whether and how long ago each of a region's forecast pages was cached."""
    region = (region_path or "").strip("/")
    if not region:
        return None
    now = time.monotonic()
    pages = []
    for page in _FORECAST_PAGES:
        cached = cache.get(
            urljoin(domain, f"/{region}/wetter/schneevorhersage/{page}/")
        )
        age = round(now - cached[0], 1) if cached is not None else None
        pages.append(
            {
                "page": page,
                "cached": cached is not None,
                "age_seconds": age,
                "fresh": age is not None and ttl is not None and age < ttl,
                "image_keys": sorted(cached[1]) if cached is not None else [],
            }
        )
    return {"region_path": region_path, "pages": pages}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BergfexConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    What a report about a resort that shows wrong or stale data needs: the
    settings in effect, whether and how the last poll failed, what each area's
    page yielded, and whether the region's shared caches are serving it.

    An entry that failed to set up is the one a report is most likely downloaded
    for, and it has no runtime_data attribute at all - setup assigns it only
    after the first refresh succeeded - so it is read with a default and the
    stored settings are reported on their own.
    """
    coordinator = getattr(entry, "runtime_data", None)
    webhook_url = entry.data.get(CONF_WEBHOOK_URL) or entry.options.get(
        CONF_WEBHOOK_URL
    )
    secrets = [webhook_url] if isinstance(webhook_url, str) and webhook_url else []

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "unique_id": entry.unique_id,
            "state": entry.state.value,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": None,
        "areas": None,
        "caches": None,
    }

    if coordinator is not None:
        interval = coordinator.update_interval
        exception = coordinator.last_exception
        # Only a TimestampDataUpdateCoordinator keeps this; the plain one does not.
        success_time = getattr(coordinator, "last_update_success_time", None)
        diagnostics["coordinator"] = {
            "name": coordinator.name,
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": _plain(success_time),
            "last_exception": (
                {
                    "type": type(exception).__name__,
                    "message": _redact_text(str(exception), secrets),
                }
                if exception is not None
                else None
            ),
            "update_interval_minutes": (
                interval.total_seconds() / 60 if interval is not None else None
            ),
        }

        resort_type = entry.data.get(CONF_TYPE, TYPE_ALPINE)
        domain = entry.data.get(CONF_DOMAIN, BASE_URL)
        # The poll caches are module state of coordinator.py, shared by every
        # entry; only the parts that concern this entry's area end up below.
        forecast_cache = _FORECAST_CACHE
        season_panel_cache = _SEASON_PANEL_CACHE
        forecast_ttl = _FORECAST_CACHE_TTL
        areas: dict[str, Any] = {}
        for area_path, area_data in (coordinator.data or {}).items():
            panel = season_panel_cache.get(area_path)
            areas[area_path] = {
                **_area_summary(area_data, resort_type),
                "cache": {
                    # Kept per area, even when empty, and only for an area
                    # configured on a subpage - the main page is the source.
                    "season_panel": {
                        "cached": panel is not None,
                        "keys": sorted(panel) if panel is not None else [],
                    },
                    # Shared by every area of the region; None without a region.
                    "forecast": _forecast_cache_info(
                        forecast_cache,
                        forecast_ttl,
                        domain,
                        area_data.get("region_path"),
                    ),
                },
            }
        diagnostics["areas"] = areas
        diagnostics["caches"] = {
            "forecast_ttl_seconds": forecast_ttl,
            "forecast_entries": len(forecast_cache),
            "season_panel_entries": len(season_panel_cache),
        }

    return async_redact_data(diagnostics, TO_REDACT)
