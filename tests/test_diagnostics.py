"""Config entry diagnostics: what a report about stale or wrong data gets to see.

The entry is set up through Home Assistant against captured pages, and the
download is fetched over the diagnostics API, so these tests also prove that
Home Assistant finds the platform and can serialise what it returns.

The HTTP layer is mocked with ``aioclient_mock``, which replaces Home
Assistant's shared client session, rather than by patching
``async_get_clientsession`` in a module - that keeps the tests independent of
which module the coordinator lives in.
"""

from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.bergfex import coordinator, diagnostics
from custom_components.bergfex.const import DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"

AREA_PATH = "/hintertux/schneebericht/"
WEBHOOK_URL = "https://usetrmnl.com/api/custom_plugins/0123abcd-4567-89ef-secret"

# The resort's main page, which a subpage entry reads the season panel from.
MAIN_PAGE_HTML = """
<div class="block" x-show="tab == 'winter'">
  <h3>Saison</h3><p>{start} - {end}</p>
</div>
"""

# The daily map first, the running total last - pages 1 to 5 carry both.
FORECAST_HTML = """
<div class="snowforecast-img">
  <a href="https://vcdn.bergfex.at/images/forecast/day.png" data-caption="Tag"></a>
</div>
<div class="snowforecast-img">
  <a href="https://vcdn.bergfex.at/images/forecast/sum.png" data-caption="Summe"></a>
</div>
"""


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def _entry(**data) -> MockConfigEntry:
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Hintertux",
        data={
            "name": "Hintertux",
            "country": "Österreich",
            "ski_area": AREA_PATH,
            "language": "at",
            "domain": "https://www.bergfex.at",
            "url": f"https://www.bergfex.at{AREA_PATH}",
            "type": "alpine",
            "webhook_url": WEBHOOK_URL,
            **data,
        },
        options={"update_interval": 45},
        source="user",
        entry_id="hintertux",
        unique_id=AREA_PATH,
    )


def _mock_bergfex(aioclient_mock) -> None:
    today = dt_util.now().date()
    season = MAIN_PAGE_HTML.format(
        start=(today - timedelta(days=30)).strftime("%d.%m.%Y"),
        end=(today + timedelta(days=30)).strftime("%d.%m.%Y"),
    )
    # First match wins, so the catch-all comes last.
    aioclient_mock.get(
        re.compile(re.escape(AREA_PATH) + "$"),
        text=_fixture("hintertux-glacier-open.html"),
    )
    aioclient_mock.get(re.compile(r"/hintertux/$"), text=season)
    aioclient_mock.get(re.compile(r"/schneevorhersage/\d/$"), text=FORECAST_HTML)
    aioclient_mock.get(re.compile(r"."), text="<html></html>")
    aioclient_mock.post(WEBHOOK_URL, text="ok")


@pytest.fixture(autouse=True)
def _empty_poll_caches():
    """The caches are module state, so a test must not inherit another's entries."""
    coordinator._FORECAST_CACHE.clear()
    coordinator._SEASON_PANEL_CACHE.clear()
    yield
    coordinator._FORECAST_CACHE.clear()
    coordinator._SEASON_PANEL_CACHE.clear()


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_diagnostics_for_a_loaded_entry(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock, hass_client
):
    """Settings, the last poll, what the page yielded and what the caches hold."""
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["entry"]["state"] == "loaded"
    assert result["entry"]["unique_id"] == AREA_PATH
    assert result["entry"]["data"]["country"] == "Österreich"
    assert result["entry"]["data"]["ski_area"] == AREA_PATH
    assert result["entry"]["data"]["type"] == "alpine"
    assert result["entry"]["data"]["language"] == "at"
    assert result["entry"]["data"]["domain"] == "https://www.bergfex.at"
    assert result["entry"]["options"] == {"update_interval": 45}

    coordinator = result["coordinator"]
    assert coordinator["last_update_success"] is True
    assert coordinator["last_exception"] is None
    assert coordinator["update_interval_minutes"] == 45

    assert list(result["areas"]) == [AREA_PATH]
    area = result["areas"][AREA_PATH]
    parsed = entry.runtime_data.data[AREA_PATH]
    assert area["keys"] == sorted(
        key for key in parsed if not key.startswith(("forecast_", "summary_"))
    )
    assert "open_pistes" in area["keys"]
    assert area["resort_name"] == "Hintertuxer Gletscher / Hintertux / Zillertal"
    assert area["region_path"] == "/tirol/"
    assert area["status"] == parsed["status"]
    assert area["operation_status"] == "täglich"
    assert area["snow_mountain"] == "25"
    assert area["snow_valley"] is None
    assert area["lifts_open_count"] == 4
    assert area["lifts_total_count"] == 21
    assert area["last_update"] == parsed["last_update"].isoformat()
    # Merged in from the main page, via the season-panel cache.
    assert area["winter_season_start"] == parsed["winter_season_start"].isoformat()
    assert area["open_pistes_count"] == len(parsed["open_pistes"])
    # A daily map from each of the six pages, a total from pages 1 to 5.
    assert area["forecast_image_count"] == 11
    # The cross-country fields do not apply to an alpine area.
    assert "classical_open_km" not in area

    cache = area["cache"]
    assert cache["season_panel"] == {
        "cached": True,
        "keys": ["winter_season_end", "winter_season_start"],
    }
    forecast = cache["forecast"]
    assert forecast["region_path"] == "/tirol/"
    assert [page["page"] for page in forecast["pages"]] == list(range(6))
    assert all(page["cached"] and page["fresh"] for page in forecast["pages"])
    assert all(page["age_seconds"] >= 0 for page in forecast["pages"])
    assert forecast["pages"][0]["image_keys"] == ["daily_caption", "daily_forecast_url"]
    assert forecast["pages"][1]["image_keys"] == [
        "daily_caption",
        "daily_forecast_url",
        "summary_caption",
        "summary_url",
    ]

    assert result["caches"] == {
        "forecast_ttl_seconds": 600,
        "forecast_entries": 6,
        "season_panel_entries": 1,
    }

    dumped = json.dumps(result)
    # Neither page markup nor the long parts of the parsed data.
    assert "<" not in dumped
    assert "vcdn.bergfex.at" not in dumped
    assert "Bichlalm" not in dumped


async def test_the_webhook_url_is_redacted_everywhere(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock, hass_client
):
    """The webhook url is what it takes to post to the display it feeds."""
    _mock_bergfex(aioclient_mock)
    entry = _entry()
    await _setup(hass, entry)
    # A failure that names the url must not carry it into the download either.
    entry.runtime_data.last_update_success = False
    entry.runtime_data.last_exception = UpdateFailed(f"Cannot reach {WEBHOOK_URL}")

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["entry"]["data"]["webhook_url"] == REDACTED
    assert result["coordinator"]["last_update_success"] is False
    assert result["coordinator"]["last_exception"] == {
        "type": "UpdateFailed",
        "message": f"Cannot reach {REDACTED}",
    }
    assert "usetrmnl" not in json.dumps(result)
    assert "secret" not in json.dumps(result)


async def test_an_entry_without_a_webhook_says_so(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock, hass_client
):
    """No url is stored as None, and None stays None rather than **REDACTED**."""
    _mock_bergfex(aioclient_mock)
    entry = _entry(webhook_url=None)
    await _setup(hass, entry)

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["entry"]["data"]["webhook_url"] is None


async def test_diagnostics_for_an_entry_that_never_set_up(
    hass: HomeAssistant, enable_custom_integrations, aioclient_mock, hass_client
):
    """The entry a report is most likely downloaded for has no runtime_data."""
    aioclient_mock.get(re.compile(r"."), status=503)
    entry = _entry()
    await _setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert not hasattr(entry, "runtime_data")

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["entry"]["state"] == "setup_retry"
    assert result["entry"]["data"]["ski_area"] == AREA_PATH
    assert result["entry"]["data"]["webhook_url"] == REDACTED
    assert result["coordinator"] is None
    assert result["areas"] is None
    assert result["caches"] is None


def test_a_cross_country_area_reports_its_trails():
    """The trail figures replace the alpine ones for a cross-country area."""
    summary = diagnostics._area_summary(
        {
            "status": "Open",
            "classical_open_km": 12,
            "classical_total_km": 40,
            "skating_open_km": 8,
        },
        "cross_country",
    )

    assert summary["keys"] == [
        "classical_open_km",
        "classical_total_km",
        "skating_open_km",
        "status",
    ]
    assert summary["classical_open_km"] == 12
    assert summary["skating_total_km"] is None
    assert "lifts_open_count" not in summary
    assert summary["open_pistes_count"] == 0
    assert summary["forecast_image_count"] == 0
