"""The region snow report's new-snow figure must come from the resort itself.

The report lists every resort of the region, and its keys are the resort paths.
A substring test matched "/ehrwald/schneebericht/" inside
"/wettersteinbahnen-ehrwald/schneebericht/", which bergfex lists first, so
Ehrwalder Alm showed the new snow of its neighbour.
"""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.bergfex.coordinator as bergfex_coordinator
from custom_components.bergfex.const import DOMAIN

AREA = "/ehrwald/schneebericht/"
REGION_REPORT = "https://www.bergfex.at/tirol/schneebericht/"

RESORT_HTML = """
<nav><ul aria-label="Breadcrumb">
  <li><a href="/">Home</a></li>
  <li><a href="/oesterreich/">Österreich</a></li>
  <li><a href="/tirol/">Tirol</a></li>
  <li><a href="/ehrwald/">Ehrwalder Almbahn</a></li>
</ul></nav>
<dt class="big">Berg (Piste, 2.000m)</dt>
<dd class="big">80 cm</dd>
"""

# Both resorts carry "ehrwald/schneebericht" in their path; the neighbour sorts
# first on bergfex.
REGION_HTML = """
<table class="snow">
  <tr><th>Resort</th></tr>
  <tr>
    <td><a href="/wettersteinbahnen-ehrwald/schneebericht/">Ehrwald Wettersteinbahnen</a></td>
    <td data-value="40">40 cm</td><td data-value="120">120 cm</td>
    <td data-value="30">30 cm</td>
    <td>3/5 <div class="icon-status icon-status1"></div></td><td>Heute</td>
  </tr>
  <tr>
    <td><a href="/ehrwald/schneebericht/">Ehrwalder Almbahn</a></td>
    <td data-value="20">20 cm</td><td data-value="90">90 cm</td>
    <td data-value="2">2 cm</td>
    <td>2/4 <div class="icon-status icon-status1"></div></td><td>Heute</td>
  </tr>
</table>
"""


class MockResponse:
    def __init__(self, text):
        self.status = 200
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        pass

    async def text(self):
        return self._text

    def raise_for_status(self):
        pass


class Session:
    def get(self, url, *args, **kwargs):
        if url == REGION_REPORT:
            return MockResponse(REGION_HTML)
        if "schneevorhersage" in url:
            return MockResponse("")
        return MockResponse(RESORT_HTML)

    def post(self, url, *args, **kwargs):
        return MockResponse("ok")


@pytest.fixture(autouse=True)
def _empty_caches():
    """The region page cache is module state; another test's copy must not leak in."""
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()
    yield
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()


@pytest.mark.asyncio
async def test_new_snow_is_taken_from_the_resort_and_not_a_neighbour_whose_path_contains_it(
    hass: HomeAssistant, enable_custom_integrations
):
    entry = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Ehrwalder Almbahn",
        data={
            "name": "Ehrwalder Almbahn",
            "country": "Österreich",
            "ski_area": AREA,
            "language": "at",
            "type": "alpine",
        },
        source="user",
        entry_id="ehrwald",
        unique_id=AREA,
    )
    entry.add_to_hass(hass)
    session = Session()
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
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.runtime_data.data[AREA]["new_snow"] == "2"
