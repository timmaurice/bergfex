"""What a poll run costs, in event loop time and in requests.

A poll parses up to nine pages per resort with lxml. That is a synchronous,
CPU-bound job, and it was running on the event loop, where it blocks every other
integration on the instance. Six of those nine pages are the region's snow
forecast, which is the same page for every resort in the region - so the work
grew with the number of resorts rather than with the number of regions.
"""

import asyncio
import threading

import pytest
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.bergfex.coordinator as bergfex_coordinator
from custom_components.bergfex.const import DOMAIN

# A breadcrumb is what the resort page's region path is read out of, and the
# region path is what the forecast urls are built from.
RESORT_HTML = """
<nav><ul aria-label="Breadcrumb">
  <li><a href="/">Home</a></li>
  <li><a href="/oesterreich/">Österreich</a></li>
  <li><a href="/{region}/">Region</a></li>
  <li><a href="/{slug}/">Resort</a></li>
</ul></nav>
<dt class="big">Berg (Piste, 3.250m)</dt>
<dd class="big">80 cm</dd>
"""

FORECAST_HTML = """
<div class="snow-forecast">
  <img src="https://vcdn.bergfex.at/images/forecast/day.png" alt="Neuschnee" />
</div>
"""


class MockResponse:
    def __init__(self, text_data, status=200):
        self.status = status
        self._text = text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        pass

    async def text(self):
        return self._text

    def raise_for_status(self):
        pass


class RecordingSession:
    """Remembers every url that was asked for."""

    def __init__(self, slug="ischgl", region="tirol"):
        self.urls: list[str] = []
        self._slug = slug
        self._region = region

    def get(self, url, *args, **kwargs):
        self.urls.append(url)
        if "schneevorhersage" in url:
            return MockResponse(FORECAST_HTML)
        return MockResponse(RESORT_HTML.format(slug=self._slug, region=self._region))

    def post(self, url, *args, **kwargs):
        return MockResponse("ok")


def _entry(*, name, path, entry_id):
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title=name,
        data={
            "name": name,
            "country": "Österreich",
            "ski_area": path,
            "language": "at",
            "type": "alpine",
        },
        source="user",
        entry_id=entry_id,
        unique_id=path,
    )


async def _setup(hass, entry, session):
    if entry.entry_id not in hass.config_entries._entries:
        entry.add_to_hass(hass)
    with patch(
        "custom_components.bergfex.coordinator.async_get_clientsession",
        return_value=session,
    ), patch(
        "custom_components.bergfex.sensor.async_get_clientsession",
        return_value=session,
    ), patch(
        "custom_components.bergfex.image.async_get_clientsession",
        return_value=session,
    ):
        if entry.state is not ConfigEntryState.LOADED:
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


@pytest.fixture(autouse=True)
def _empty_forecast_cache():
    """The cache is module state, so a test must not inherit another's entries."""
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()
    yield
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()


@pytest.mark.asyncio
async def test_pages_are_parsed_off_the_event_loop(
    hass: HomeAssistant, enable_custom_integrations
):
    """lxml is synchronous and CPU-bound, so it belongs in the executor.

    Running it on the loop stalls every other integration on the instance for
    the duration - nine pages per resort, on every poll.
    """
    loop_thread = threading.current_thread()
    parse_threads: list[threading.Thread] = []

    real_resort = bergfex_coordinator.parse_resort_page
    real_forecast = bergfex_coordinator.parse_snow_forecast_images

    def recording_resort(*args, **kwargs):
        parse_threads.append(threading.current_thread())
        return real_resort(*args, **kwargs)

    def recording_forecast(*args, **kwargs):
        parse_threads.append(threading.current_thread())
        return real_forecast(*args, **kwargs)

    entry = _entry(name="Ischgl", path="/ischgl/schneebericht/", entry_id="thread")
    with patch.object(
        bergfex_coordinator, "parse_resort_page", recording_resort
    ), patch.object(
        bergfex_coordinator, "parse_snow_forecast_images", recording_forecast
    ):
        await _setup(hass, entry, RecordingSession())

    assert parse_threads, "no page was parsed at all"
    assert loop_thread not in parse_threads


@pytest.mark.asyncio
async def test_a_regions_forecast_pages_are_fetched_once(
    hass: HomeAssistant, enable_custom_integrations
):
    """Two resorts of one region must not fetch the same six pages twice.

    The forecast urls are built from the region path, so they are identical for
    both. Fetching and re-parsing them per resort made the cost of a poll scale
    with the resort count instead of the region count.
    """
    first_session = RecordingSession(slug="ischgl")
    second_session = RecordingSession(slug="soelden")

    await _setup(
        hass,
        _entry(name="Ischgl", path="/ischgl/schneebericht/", entry_id="one"),
        first_session,
    )
    first_forecasts = [u for u in first_session.urls if "schneevorhersage" in u]
    assert len(first_forecasts) == 6, "the first resort should fetch all six pages"

    await _setup(
        hass,
        _entry(name="Sölden", path="/soelden/schneebericht/", entry_id="two"),
        second_session,
    )
    second_forecasts = [u for u in second_session.urls if "schneevorhersage" in u]

    assert set(first_forecasts) == {
        f"https://www.bergfex.at/tirol/wetter/schneevorhersage/{i}/" for i in range(6)
    }
    assert second_forecasts == [], "the second resort refetched the region's pages"


@pytest.mark.asyncio
async def test_a_different_region_is_still_fetched(
    hass: HomeAssistant, enable_custom_integrations
):
    """The cache is keyed on the url, so another region is not served from it."""
    await _setup(
        hass,
        _entry(name="Ischgl", path="/ischgl/schneebericht/", entry_id="tirol"),
        RecordingSession(),
    )

    salzburg = RecordingSession(slug="saalbach", region="salzburg")
    await _setup(
        hass,
        _entry(name="Saalbach", path="/saalbach/schneebericht/", entry_id="salzburg"),
        salzburg,
    )

    assert [u for u in salzburg.urls if "/salzburg/wetter/schneevorhersage/" in u]


def _cross_country_entry(*, name, path, entry_id):
    entry = _entry(name=name, path=path, entry_id=entry_id)
    entry = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title=name,
        data={**entry.data, "type": "cross_country"},
        source="user",
        entry_id=entry_id,
        unique_id=path,
    )
    return entry


@pytest.mark.asyncio
async def test_a_regions_snow_report_is_fetched_once(
    hass: HomeAssistant, enable_custom_integrations
):
    """The region snow report lists every resort of the region, so one is enough.

    It was fetched per resort: the five resorts of Les 3 Vallées asked for the
    same page five times on every poll.
    """
    report = "https://www.bergfex.at/tirol/schneebericht/"
    first_session = RecordingSession(slug="ischgl")
    second_session = RecordingSession(slug="soelden")

    await _setup(
        hass,
        _entry(name="Ischgl", path="/ischgl/schneebericht/", entry_id="one"),
        first_session,
    )
    await _setup(
        hass,
        _entry(name="Sölden", path="/soelden/schneebericht/", entry_id="two"),
        second_session,
    )

    assert first_session.urls.count(report) == 1
    assert report not in second_session.urls, "the second resort refetched it"


@pytest.mark.asyncio
async def test_a_countrys_cross_country_overview_is_fetched_once(
    hass: HomeAssistant, enable_custom_integrations
):
    """The overview carries the trail totals of every area in the country."""
    overview = "https://www.bergfex.at/oesterreich/langlaufen/loipenberichte/"
    first_session = RecordingSession()
    second_session = RecordingSession()

    await _setup(
        hass,
        _cross_country_entry(
            name="Absam", path="/tirol/langlaufen/absam/", entry_id="absam"
        ),
        first_session,
    )
    await _setup(
        hass,
        _cross_country_entry(
            name="Almtal",
            path="/oberoesterreich/langlaufen/almtal-gruenau/",
            entry_id="almtal",
        ),
        second_session,
    )

    assert first_session.urls.count(overview) == 1
    assert overview not in second_session.urls, "the second area refetched it"
    # Each area's own trail report is still its own.
    assert (
        "https://www.bergfex.at/oberoesterreich/langlaufen/almtal-gruenau/loipen/"
        in (second_session.urls)
    )


@pytest.mark.asyncio
async def test_polls_running_at_once_share_one_request(hass: HomeAssistant):
    """The coordinators poll in step, so the cache alone is too late.

    Every one of them asks before the first answer is in. They must wait on the
    request already under way rather than send their own.
    """
    release = asyncio.Event()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        await release.wait()
        return {"new_snow": "5 cm"}

    key = ("https://www.bergfex.at/tirol/schneebericht/", "at")
    waiting = [
        hass.async_create_task(
            bergfex_coordinator._async_shared(
                hass, bergfex_coordinator._REGION_PAGE_CACHE, key, 600, fetch
            )
        )
        for _ in range(5)
    ]
    await asyncio.sleep(0)
    release.set()
    results = await asyncio.gather(*waiting)

    assert calls == 1
    assert results == [{"new_snow": "5 cm"}] * 5
    assert key not in bergfex_coordinator._IN_FLIGHT


@pytest.mark.asyncio
async def test_a_page_that_could_not_be_read_is_asked_for_again(
    hass: HomeAssistant,
):
    """Only an answer is cached. A refusal must not stick for the whole TTL."""
    answers = iter([None, {"new_snow": "5 cm"}])

    async def fetch():
        return next(answers)

    key = ("https://www.bergfex.de/bayern/schneebericht/", "at")
    cache = bergfex_coordinator._REGION_PAGE_CACHE

    assert await bergfex_coordinator._async_shared(hass, cache, key, 600, fetch) is None
    assert key not in cache
    assert await bergfex_coordinator._async_shared(hass, cache, key, 600, fetch) == {
        "new_snow": "5 cm"
    }
