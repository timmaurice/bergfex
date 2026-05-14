import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from custom_components.bergfex.__init__ import async_setup_entry
from custom_components.bergfex.const import DOMAIN, COORDINATORS
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={
            "name": "Test Resort",
            "country": "Italien",
            "ski_area": "/it/test/schneebericht/",
            "language": "it",
            "type": "alpine",
        },
        source="user",
        entry_id="test_entry_id",
    )


@pytest.mark.asyncio
async def test_async_update_data_resort_fallback(
    hass: HomeAssistant, mock_config_entry
):
    """Test that main page is fetched and seasonal variables are copied when season_start is missing."""

    # Setup mock HTMLs
    subpage_html = """
    <dt>Tageskarte:</dt>
    <dd>€ 75,00</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    main_page_html = """
    <dt>Tageskarte:</dt>
    <dd>€ 75,00</dd>
    <dt>Stagione:</dt>
    <dd>13.12.2025 - 11.04.2026</dd>
    <dt>Orario:</dt>
    <dd>09:00 - 16:45</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
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

    class MockSession:
        def get(self, url, *args, **kwargs):
            if "schneebericht" in url or "forecast" in url or "schneewerte" in url:
                return MockResponse(subpage_html)
            return MockResponse(main_page_html)

        def post(self, url, *args, **kwargs):
            return MockResponse("ok")

    mock_session = MockSession()

    # We mock async_get_clientsession to return our mock_session
    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=mock_session,
    ), patch("custom_components.bergfex.__init__.datetime") as mock_datetime, patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ) as mock_refresh, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):

        # Mock today to be outside the season (e.g., May 14, 2026)
        from datetime import datetime, date

        mock_now = datetime(2026, 5, 14, 12, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime

        mock_config_entry.add_to_hass(hass)
        await async_setup_entry(hass, mock_config_entry)

        coordinator = hass.data[DOMAIN][COORDINATORS]["bergfex_Test Resort"]
        # Manually trigger the update method since we mocked first_refresh
        await coordinator.async_refresh()

        data = coordinator.data

        assert data is not None
        area_data = data.get("/it/test/schneebericht/")

        assert area_data is not None
        assert area_data["status"] == "Closed"
        assert area_data["season_start"] == date(2025, 12, 13)
        assert area_data["season_end"] == date(2026, 4, 11)
        assert area_data["operating_hours_start"] == "09:00"
        assert area_data["operating_hours_end"] == "16:45"


@pytest.mark.asyncio
async def test_async_update_data_resort_fallback_active_season(
    hass: HomeAssistant, mock_config_entry
):
    """Test that main page is fetched and resort is Open when inside the season."""

    # Setup mock HTMLs
    subpage_html = """
    <dt>Tageskarte:</dt>
    <dd>€ 75,00</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    main_page_html = """
    <dt>Tageskarte:</dt>
    <dd>€ 75,00</dd>
    <dt>Stagione:</dt>
    <dd>13.12.2025 - 11.04.2026</dd>
    <dt>Orario:</dt>
    <dd>09:00 - 16:45</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
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

    class MockSession:
        def get(self, url, *args, **kwargs):
            if "schneebericht" in url or "forecast" in url or "schneewerte" in url:
                return MockResponse(subpage_html)
            return MockResponse(main_page_html)

        def post(self, url, *args, **kwargs):
            return MockResponse("ok")

    mock_session = MockSession()

    # We mock async_get_clientsession to return our mock_session
    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=mock_session,
    ), patch("custom_components.bergfex.__init__.datetime") as mock_datetime, patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ) as mock_refresh, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):

        # Mock today to be INSIDE the season and operating hours (e.g., Jan 15, 2026 at 12:00)
        from datetime import datetime, date

        mock_now = datetime(2026, 1, 15, 12, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime

        mock_config_entry.add_to_hass(hass)
        await async_setup_entry(hass, mock_config_entry)

        coordinator = hass.data[DOMAIN][COORDINATORS]["bergfex_Test Resort"]
        # Manually trigger the update method since we mocked first_refresh
        await coordinator.async_refresh()

        data = coordinator.data

        assert data is not None
        area_data = data.get("/it/test/schneebericht/")

        assert area_data is not None
        assert area_data["status"] == "Open"
        assert area_data["season_start"] == date(2025, 12, 13)
        assert area_data["season_end"] == date(2026, 4, 11)
        assert area_data["operating_hours_start"] == "09:00"
        assert area_data["operating_hours_end"] == "16:45"
