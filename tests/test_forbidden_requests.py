"""What has to survive when bergfex turns a request away.

A user reported `403, message='Forbidden'` on every entry and nothing else was
knowable from it: not whether an address had been blocked, a rate limit hit or a
rule matched, and not even which url had been asked for - bergfex redirects
German resorts from .at to .de, so the error named a host the integration never
chose. These tests pin the evidence that makes the next such report answerable
in one round instead of three.
"""

import logging

import pytest
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex import refusal
from custom_components.bergfex.__init__ import async_setup_entry
from custom_components.bergfex.const import DOMAIN
from custom_components.bergfex.fetch import (
    EXCERPT_BYTES,
    BergfexRefused,
    async_fetch_text,
)
from custom_components.bergfex.refusal import (
    REFUSAL_THRESHOLD,
    REQUESTS_REFUSED_ISSUE_ID,
)

AREA_PATH = "/liftverbund-feldberg/schneebericht/"
REQUESTED = f"https://www.bergfex.at{AREA_PATH}"
# Where bergfex sends a German resort, and what the reporter's log named.
FINAL = f"https://www.bergfex.de{AREA_PATH}"
BLOCK_PAGE = (
    b"<html><head><title>Attention Required!</title></head><body>" + b"x" * 4000
)


@pytest.fixture(autouse=True)
def _clear_module_state():
    """Both of these are module state keyed on entry id, and the ids repeat.

    `_SETUP_FAILURE_LOGGED` is what keeps a failing setup from warning on every
    retry, so a test that counts warnings has to start from empty or it inherits
    the previous test's entry.
    """
    from custom_components.bergfex import __init__ as bergfex_init

    refusal._STATE.clear()
    bergfex_init._SETUP_FAILURE_LOGGED.clear()
    yield
    refusal._STATE.clear()
    bergfex_init._SETUP_FAILURE_LOGGED.clear()


def _entry(entry_id="test_entry_id", title="Feldberg"):
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title=title,
        data={
            "name": title,
            "country": "Deutschland",
            "ski_area": AREA_PATH,
            "language": "at",
            "domain": "https://www.bergfex.at",
            "type": "alpine",
        },
        source="user",
        entry_id=entry_id,
    )


@pytest.fixture
def mock_config_entry():
    return _entry()


class _Content:
    """Records how much of the body was asked for."""

    def __init__(self, payload):
        self._payload = payload
        self.reads = []

    async def read(self, size):
        self.reads.append(size)
        return self._payload[:size]


class _Response:
    def __init__(self, status, *, body=b"", headers=None, url=FINAL):
        self.status = status
        self.url = url
        self.headers = headers or {}
        self.content = _Content(body)
        self.text_calls = 0

    async def text(self):
        self.text_calls += 1
        return "<html>ok</html>"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    """Answers every request the same way, which is how a block looks."""

    def __init__(self, response_factory):
        self._factory = response_factory
        self.responses = []
        self.requests = []

    def get(self, url, *args, **kwargs):
        self.requests.append(url)
        response = self._factory()
        self.responses.append(response)
        return response

    def post(self, url, *args, **kwargs):
        raise OSError("no webhook in these tests")


def _refused_session(status=403, headers=None):
    return _Session(
        lambda: _Response(
            status,
            body=BLOCK_PAGE,
            headers=(
                headers
                if headers is not None
                else {"cf-ray": "8f0a1b2c3d4e5f67-FRA", "server": "cloudflare"}
            ),
        )
    )


# --- what the exception carries -------------------------------------------


@pytest.mark.asyncio
async def test_a_refusal_names_both_urls_and_the_ray_id():
    session = _refused_session()

    with pytest.raises(BergfexRefused) as raised:
        await async_fetch_text(session, REQUESTED)

    err = raised.value
    assert err.status == 403
    assert err.requested_url == REQUESTED
    assert err.final_url == FINAL
    assert err.cf_ray == "8f0a1b2c3d4e5f67-FRA"
    assert err.host == "www.bergfex.de"
    # The redirect is the whole reason the reporter saw a host nobody configured.
    assert REQUESTED in str(err) and FINAL in str(err)
    assert "8f0a1b2c3d4e5f67-FRA" in str(err)


@pytest.mark.asyncio
async def test_the_page_is_not_pulled_in_to_be_thrown_away():
    """A bergfex page is ~200 KB. None of it belongs in a log line."""
    session = _refused_session()

    with pytest.raises(BergfexRefused) as raised:
        await async_fetch_text(session, REQUESTED)

    response = session.responses[0]
    assert response.text_calls == 0
    assert response.content.reads == [EXCERPT_BYTES]
    assert len(raised.value.excerpt) <= EXCERPT_BYTES
    assert "Attention Required" in raised.value.excerpt


@pytest.mark.asyncio
async def test_the_excerpt_stays_out_of_the_message():
    """It goes to diagnostics and debug, not into every log line."""
    session = _refused_session()

    with pytest.raises(BergfexRefused) as raised:
        await async_fetch_text(session, REQUESTED)

    assert "Attention Required" not in str(raised.value)


@pytest.mark.asyncio
async def test_a_page_that_loads_is_returned_unchanged():
    session = _Session(lambda: _Response(200, url=REQUESTED))

    assert await async_fetch_text(session, REQUESTED) == "<html>ok</html>"
    assert session.responses[0].content.reads == []


@pytest.mark.asyncio
async def test_a_missing_page_is_not_a_refusal():
    """A 404 is a wrong path; saying "blocked" would send the user after the wrong thing."""
    session = _Session(lambda: _Response(404, body=b"nope"))

    with pytest.raises(BergfexRefused) as raised:
        await async_fetch_text(session, REQUESTED)

    assert raised.value.is_refusal is False


# --- the repair issue ------------------------------------------------------


def _issue(hass, host="www.bergfex.de"):
    return ir.async_get(hass).async_get_issue(
        DOMAIN, f"{REQUESTS_REFUSED_ISSUE_ID}_{host}"
    )


async def _fail_setup(hass, entry, session):
    with patch(
        "custom_components.bergfex.coordinator.async_get_clientsession",
        return_value=session,
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with pytest.raises(ConfigEntryNotReady) as raised:
            await async_setup_entry(hass, entry)
    return raised.value


@pytest.mark.asyncio
async def test_the_reason_reaches_the_entry_page(
    hass: HomeAssistant, mock_config_entry
):
    mock_config_entry.add_to_hass(hass)
    err = await _fail_setup(hass, mock_config_entry, _refused_session())

    message = str(err)
    assert "403" in message
    assert FINAL in message
    assert "8f0a1b2c3d4e5f67-FRA" in message


@pytest.mark.asyncio
async def test_a_short_outage_raises_nothing(hass: HomeAssistant, mock_config_entry):
    """Four refusals is about a minute. A restart looks like that."""
    mock_config_entry.add_to_hass(hass)

    for _ in range(REFUSAL_THRESHOLD - 1):
        await _fail_setup(hass, mock_config_entry, _refused_session())

    assert _issue(hass) is None


@pytest.mark.asyncio
async def test_a_persistent_refusal_is_reported(hass: HomeAssistant, mock_config_entry):
    mock_config_entry.add_to_hass(hass)

    for _ in range(REFUSAL_THRESHOLD):
        await _fail_setup(hass, mock_config_entry, _refused_session())

    issue = _issue(hass)
    assert issue is not None
    assert issue.is_fixable is False
    assert issue.is_persistent is True
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.translation_placeholders["host"] == "www.bergfex.de"
    assert issue.translation_placeholders["status"] == "403"
    assert issue.translation_placeholders["cf_ray"] == "8f0a1b2c3d4e5f67-FRA"


@pytest.mark.asyncio
async def test_one_page_through_takes_it_away(hass: HomeAssistant, mock_config_entry):
    mock_config_entry.add_to_hass(hass)
    for _ in range(REFUSAL_THRESHOLD):
        await _fail_setup(hass, mock_config_entry, _refused_session())
    assert _issue(hass) is not None

    coordinator_session = _Session(lambda: _Response(200, url=REQUESTED))
    with patch(
        "custom_components.bergfex.coordinator.async_get_clientsession",
        return_value=coordinator_session,
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ):
        mock_config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        assert await async_setup_entry(hass, mock_config_entry) is True

    assert _issue(hass) is None


@pytest.mark.asyncio
async def test_three_resorts_behind_one_block_are_one_message(hass: HomeAssistant):
    """One condition, one thing for the user to do. Three cards would be noise."""
    entries = [
        _entry("entry_feldberg", "Feldberg"),
        _entry("entry_gschwend", "Gschwend"),
        _entry("entry_grosserlach", "Grosserlach"),
    ]
    for entry in entries:
        entry.add_to_hass(hass)

    for _ in range(REFUSAL_THRESHOLD):
        for entry in entries:
            await _fail_setup(hass, entry, _refused_session())

    issues = [
        issue
        for issue in ir.async_get(hass).issues.values()
        if issue.domain == DOMAIN and REQUESTS_REFUSED_ISSUE_ID in issue.issue_id
    ]
    assert len(issues) == 1
    named = issues[0].translation_placeholders["resorts"]
    assert all(entry.title in named for entry in entries)


@pytest.mark.asyncio
async def test_a_wrong_path_never_raises_it(hass: HomeAssistant, mock_config_entry):
    mock_config_entry.add_to_hass(hass)
    session_404 = _Session(lambda: _Response(404, body=b"nope"))

    for _ in range(REFUSAL_THRESHOLD + 2):
        await _fail_setup(hass, mock_config_entry, session_404)

    assert _issue(hass) is None


@pytest.mark.asyncio
async def test_it_stays_as_quiet_as_before(
    hass: HomeAssistant, mock_config_entry, caplog
):
    """The one warning a failed setup is allowed. The evidence rides inside it."""
    caplog.set_level(logging.DEBUG)
    mock_config_entry.add_to_hass(hass)

    for _ in range(REFUSAL_THRESHOLD):
        await _fail_setup(hass, mock_config_entry, _refused_session())

    warnings = [
        record
        for record in caplog.records
        if record.levelno >= logging.WARNING
        and "custom_components/bergfex" in record.pathname
    ]
    assert len(warnings) == 1
    assert "403" in warnings[0].getMessage()


# --- the config flow ------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [(403, "refused"), (429, "refused"), (451, "refused"), (404, "cannot_connect")],
)
@pytest.mark.asyncio
async def test_the_setup_dialog_tells_the_two_apart(
    hass: HomeAssistant, status, expected
):
    """ "Check your internet connection" is the wrong advice for a block.

    The connection is fine; bergfex is turning it away. Sending somebody to
    their router over that costs them an evening.
    """
    from custom_components.bergfex.config_flow import async_page_check

    with patch(
        "custom_components.bergfex.config_flow.async_get_clientsession",
        return_value=_Session(lambda: _Response(status, body=BLOCK_PAGE)),
    ):
        assert await async_page_check(hass, REQUESTED) == expected


@pytest.mark.asyncio
async def test_a_page_that_serves_is_no_problem(hass: HomeAssistant):
    from custom_components.bergfex.config_flow import async_page_check

    with patch(
        "custom_components.bergfex.config_flow.async_get_clientsession",
        return_value=_Session(lambda: _Response(200, url=REQUESTED)),
    ):
        assert await async_page_check(hass, REQUESTED) is None


@pytest.mark.asyncio
async def test_every_language_can_say_it_was_refused(hass: HomeAssistant):
    """A missing key renders as the raw string in that user's dialog."""
    import json
    from pathlib import Path

    folder = Path("custom_components/bergfex/translations")
    for path in sorted(folder.glob("*.json")):
        errors = json.loads(path.read_text())["config"]["error"]
        assert "refused" in errors, path.name
        assert errors["refused"].strip(), path.name


def test_the_repair_card_names_the_way_out():
    """It is read by somebody who cannot reach the host, so it has to be actionable.

    Switching an entry to another language moves it to another bergfex domain,
    and only the German one redirects German resorts to the refused host. That
    was verified against a live installation before it was written down here.
    """
    import json
    from pathlib import Path

    for path in sorted(Path("custom_components/bergfex/translations").glob("*.json")):
        issue = json.loads(path.read_text())["issues"]["requests_refused"]
        for placeholder in ("{host}", "{status}", "{resorts}", "{cf_ray}"):
            assert placeholder in issue["description"], (path.name, placeholder)
        assert "{host}" in issue["title"], path.name
