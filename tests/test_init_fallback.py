import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from custom_components.bergfex.__init__ import (
    DUPLICATE_ENTRY_ISSUE_ID,
    async_remove_entry,
    async_setup_entry,
)
from custom_components.bergfex.config_flow import entry_area_name
from custom_components.bergfex.const import DOMAIN, COORDINATORS
from custom_components.bergfex.unique_id import coordinator_key
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
    """Test that the main page is fetched and the winter period is copied across."""

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
    <dt>Orario:</dt>
    <dd>09:00 - 16:45</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Stagione</h3><p>13.12.2025 - 11.04.2026</p>
      <h3>Orario</h3><p>09:00 - 16:45</p>
    </div>
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
    ), patch("custom_components.bergfex.parser.datetime") as mock_datetime, patch(
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

        coordinator = hass.data[DOMAIN][COORDINATORS][
            coordinator_key("/it/test/schneebericht/")
        ]
        # Manually trigger the update method since we mocked first_refresh
        await coordinator.async_refresh()

        data = coordinator.data

        assert data is not None
        area_data = data.get("/it/test/schneebericht/")

        assert area_data is not None
        # No snow reported, so not skiable - the season dates no longer decide this.
        assert area_data["status"] == "Closed"
        assert area_data["winter_season_start"] == date(2025, 12, 13)
        assert area_data["winter_season_end"] == date(2026, 4, 11)
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
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">80 cm</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    main_page_html = """
    <dt>Tageskarte:</dt>
    <dd>€ 75,00</dd>
    <dt>Orario:</dt>
    <dd>09:00 - 16:45</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Stagione</h3><p>13.12.2025 - 11.04.2026</p>
      <h3>Orario</h3><p>09:00 - 16:45</p>
    </div>
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
    ), patch("custom_components.bergfex.parser.datetime") as mock_datetime, patch(
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

        coordinator = hass.data[DOMAIN][COORDINATORS][
            coordinator_key("/it/test/schneebericht/")
        ]
        # Manually trigger the update method since we mocked first_refresh
        await coordinator.async_refresh()

        data = coordinator.data

        assert data is not None
        area_data = data.get("/it/test/schneebericht/")

        assert area_data is not None
        assert area_data["status"] == "Open"
        assert area_data["winter_season_start"] == date(2025, 12, 13)
        assert area_data["winter_season_end"] == date(2026, 4, 11)
        assert area_data["operating_hours_start"] == "09:00"
        assert area_data["operating_hours_end"] == "16:45"


@pytest.mark.asyncio
async def test_setup_backfills_the_unique_id(hass: HomeAssistant, mock_config_entry):
    """Entries from before the flow set a unique id must gain one on setup.

    Without it the duplicate check in the config flow never fires for a resort
    that is already installed, which is what let the same resort be added twice.
    """

    class MockResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *error_info):
            pass

        async def text(self):
            return ""

        def raise_for_status(self):
            pass

    class MockSession:
        def get(self, url, *args, **kwargs):
            return MockResponse()

        def post(self, url, *args, **kwargs):
            return MockResponse()

    mock_config_entry.add_to_hass(hass)
    assert mock_config_entry.unique_id is None

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=MockSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        await async_setup_entry(hass, mock_config_entry)

    assert mock_config_entry.unique_id == "/it/test/schneebericht/"


class _StubResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *error_info):
        pass

    async def text(self):
        return ""

    def raise_for_status(self):
        pass


class _StubSession:
    def get(self, url, *args, **kwargs):
        return _StubResponse()

    def post(self, url, *args, **kwargs):
        return _StubResponse()


def _legacy_entry(entry_id: str, ski_area: str) -> MockConfigEntry:
    """An entry from before the config flow assigned a unique id."""
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={
            "name": "Test Resort",
            "country": "Italien",
            "ski_area": ski_area,
            "language": "it",
            "type": "alpine",
        },
        source="user",
        entry_id=entry_id,
    )


@pytest.mark.asyncio
async def test_backfill_skips_an_id_another_entry_already_has(hass: HomeAssistant):
    """Two legacy entries for one resort must not both be given the same id.

    Home Assistant rejects the second assignment, logs an error asking the user
    to file a bug against this integration, and raises its own collision repair -
    on every single restart. Only the first entry may take the id; the leftover
    is surfaced as a repair the user can actually act on.
    """
    ski_area = "/it/test/schneebericht/"
    first = _legacy_entry("first_entry", ski_area)
    second = _legacy_entry("second_entry", ski_area)
    first.add_to_hass(hass)
    second.add_to_hass(hass)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_StubSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        await async_setup_entry(hass, first)
        await async_setup_entry(hass, second)

    assert first.unique_id == ski_area
    assert second.unique_id is None

    registry = ir.async_get(hass)
    assert (
        registry.async_get_issue(DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_first_entry")
        is None
    )
    issue = registry.async_get_issue(DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry")
    assert issue is not None
    assert issue.translation_key == DUPLICATE_ENTRY_ISSUE_ID
    assert issue.translation_placeholders["path"] == ski_area


@pytest.mark.asyncio
async def test_duplicate_issue_goes_away_with_the_duplicate_entry(hass: HomeAssistant):
    """Deleting the leftover entry is the fix, so the repair must clear with it."""
    ski_area = "/it/test/schneebericht/"
    first = _legacy_entry("first_entry", ski_area)
    second = _legacy_entry("second_entry", ski_area)
    first.add_to_hass(hass)
    second.add_to_hass(hass)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_StubSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        await async_setup_entry(hass, first)
        await async_setup_entry(hass, second)

    registry = ir.async_get(hass)
    assert (
        registry.async_get_issue(DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry")
        is not None
    )

    await async_remove_entry(hass, second)

    assert (
        registry.async_get_issue(DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry")
        is None
    )


async def _setup_two_duplicates(hass: HomeAssistant):
    """Set up two legacy entries for one resort, as a user who hit the bug has."""
    ski_area = "/it/test/schneebericht/"
    first = _legacy_entry("first_entry", ski_area)
    second = _legacy_entry("second_entry", ski_area)
    first.add_to_hass(hass)
    second.add_to_hass(hass)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_StubSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        await async_setup_entry(hass, first)
        await async_setup_entry(hass, second)

    return first, second


@pytest.mark.asyncio
async def test_duplicate_issue_names_the_entry_it_is_about(hass: HomeAssistant):
    """Both entries carry the same title, so the title cannot identify either.

    The issue has to say which of the two rows it means - and be fixable, so the
    user does not have to tell them apart at all.
    """
    _, second = await _setup_two_duplicates(hass)

    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry"
    )
    assert issue is not None
    assert issue.translation_placeholders["entry_id"] == second.entry_id
    assert issue.is_fixable is True
    assert issue.data == {"entry_id": second.entry_id}


@pytest.mark.asyncio
async def test_deleting_the_entry_that_won_the_id_hands_it_over(
    hass: HomeAssistant, enable_custom_integrations
):
    """The user may delete either row, and either choice has to resolve it.

    Deleting the entry that holds the unique id used to leave the survivor
    without an id and with its repair issue still raised, until the next restart.
    """
    first, second = await _setup_two_duplicates(hass)
    assert first.unique_id == "/it/test/schneebericht/"
    assert second.unique_id is None

    await hass.config_entries.async_remove(first.entry_id)
    await hass.async_block_till_done()

    assert second.unique_id == "/it/test/schneebericht/"
    assert (
        ir.async_get(hass).async_get_issue(
            DOMAIN, f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry"
        )
        is None
    )


@pytest.mark.asyncio
async def test_the_repair_deletes_the_duplicate_entry(
    hass: HomeAssistant, enable_custom_integrations
):
    """Pressing "Fix" has to remove the entry the issue is about, and only it."""
    first, second = await _setup_two_duplicates(hass)

    assert await async_setup_component(hass, "repairs", {})
    hass.config.components.add(DOMAIN)

    flow_manager = hass.data["repairs"]["flow_manager"]
    issue_id = f"{DUPLICATE_ENTRY_ISSUE_ID}_second_entry"

    result = await flow_manager.async_init(DOMAIN, data={"issue_id": issue_id})
    assert result["type"] == FlowResultType.FORM
    assert result["description_placeholders"]["entry_id"] == second.entry_id

    result = await flow_manager.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    remaining = hass.config_entries.async_entries(DOMAIN)
    assert [entry.entry_id for entry in remaining] == [first.entry_id]
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.asyncio
async def test_setup_survives_an_entry_without_a_name(hass: HomeAssistant):
    """An entry whose data has no "name" must still set up.

    The config flow always writes the key, but a hand-edited entry or one
    restored from an older backup does not have it, and reading it unguarded
    aborted setup with a bare KeyError instead of a usable message.
    """
    entry = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={
            "country": "Italien",
            "ski_area": "/it/test/schneebericht/",
            "language": "it",
            "type": "alpine",
        },
        source="user",
        entry_id="nameless_entry",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.bergfex.__init__.async_get_clientsession",
        return_value=_StubSession(),
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.async_config_entry_first_refresh"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        assert await async_setup_entry(hass, entry) is True

    assert coordinator_key("/it/test/schneebericht/") in hass.data[DOMAIN][COORDINATORS]


def test_entry_area_name_falls_back_to_the_resort_slug():
    """The fallback is the name the flow itself writes for an unlisted resort.

    Anything else would hand legacy_unique_id_prefixes a string the flow never
    wrote, so the entity migration would look for prefixes that never existed.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"ski_area": "/oesterreich/ischgl/schneebericht/"},
    )
    assert entry_area_name(entry) == "ischgl"

    named = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Ischgl", "ski_area": "/oesterreich/ischgl/schneebericht/"},
    )
    assert entry_area_name(named) == "Ischgl"
