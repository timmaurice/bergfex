"""What a poll sends to the entry's webhook."""

import json as _json
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.const import CONF_WEBHOOK_URL, DOMAIN
from custom_components.bergfex.coordinator import BergfexCoordinator

WEBHOOK_URL = "https://hooks.example.com/bergfex"


class MockResponse:
    def __init__(self, text_data="", status=200):
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
    """Answers every page with nothing and remembers what was posted."""

    def __init__(self):
        self.posts: list[tuple[str, dict]] = []

    def get(self, url, *args, **kwargs):
        return MockResponse()

    def post(self, url, *args, json=None, **kwargs):
        # aiohttp encodes json= with json.dumps before anything is sent, so a
        # value it cannot write fails the post here just as it does there.
        _json.dumps(json)
        self.posts.append((url, json))
        return MockResponse("ok")


@pytest.mark.asyncio
async def test_webhook_drops_only_last_update(
    hass: HomeAssistant, enable_custom_integrations
):
    """last_update is left out because it is a datetime, and nothing else is.

    The filter was `k not in ("last_update")` - a bare string, so a substring
    test that also dropped every key spelled inside "last_update". No key the
    parser writes today is one, but "date", "update" or "last" would have
    vanished from the payload without a word.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ischgl",
        unique_id="/ischgl/",
        data={
            "name": "Ischgl",
            "country": "Österreich",
            "ski_area": "/ischgl/",
            "language": "at",
            "type": "alpine",
            CONF_WEBHOOK_URL: WEBHOOK_URL,
        },
    )
    entry.add_to_hass(hass)

    parsed = {
        "last_update": datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc),
        "snow_mountain": "80 cm",
        "date": "10.01.2026",
        "update": "daily",
        "last": "yes",
    }
    session = RecordingSession()
    with (
        patch(
            "custom_components.bergfex.coordinator.async_get_clientsession",
            return_value=session,
        ),
        patch(
            "custom_components.bergfex.coordinator.parse_resort_page",
            return_value=dict(parsed),
        ),
    ):
        coordinator = BergfexCoordinator(hass, entry)
        await coordinator._async_update_data()

    assert len(session.posts) == 1
    url, body = session.posts[0]
    assert url == WEBHOOK_URL
    sent = body["merge_variables"]
    assert "last_update" not in sent
    for key in ("snow_mountain", "date", "update", "last"):
        assert sent[key] == parsed[key]


@pytest.mark.asyncio
async def test_webhook_sends_season_dates_as_iso(
    hass: HomeAssistant, enable_custom_integrations
):
    """The season panel's dates go out as ISO 8601 strings.

    They are datetime.date objects, which json.dumps refuses: the post raised
    TypeError, was logged as an error, and the webhook never fired for any
    resort that publishes a season panel.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ischgl",
        unique_id="/ischgl/",
        data={
            "name": "Ischgl",
            "country": "Österreich",
            "ski_area": "/ischgl/",
            "language": "at",
            "type": "alpine",
            CONF_WEBHOOK_URL: WEBHOOK_URL,
        },
    )
    entry.add_to_hass(hass)

    parsed = {
        "last_update": datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc),
        "snow_mountain": "80 cm",
        "winter_season_start": date(2026, 12, 5),
        "winter_season_end": date(2027, 4, 18),
        "winter_operating_hours_start": "08:30",
        "winter_operating_hours_end": "16:30",
        "summer_season_start": date(2026, 6, 20),
        "summer_season_end": date(2026, 9, 27),
    }
    session = RecordingSession()
    with (
        patch(
            "custom_components.bergfex.coordinator.async_get_clientsession",
            return_value=session,
        ),
        patch(
            "custom_components.bergfex.coordinator.parse_resort_page",
            return_value=dict(parsed),
        ),
    ):
        coordinator = BergfexCoordinator(hass, entry)
        await coordinator._async_update_data()

    assert len(session.posts) == 1
    url, body = session.posts[0]
    assert url == WEBHOOK_URL
    _json.dumps(body)
    sent = body["merge_variables"]
    assert sent["winter_season_start"] == "2026-12-05"
    assert sent["winter_season_end"] == "2027-04-18"
    assert sent["summer_season_start"] == "2026-06-20"
    assert sent["summer_season_end"] == "2026-09-27"
    assert sent["winter_operating_hours_start"] == "08:30"
    assert sent["winter_operating_hours_end"] == "16:30"
    assert sent["snow_mountain"] == "80 cm"
    assert "last_update" not in sent
