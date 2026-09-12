"""Tests for adding a resort through the config flow."""

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.config_flow import (
    InvalidSkiAreaPath,
    normalize_ski_area_path,
    ski_area_name_from_path,
)
from custom_components.bergfex.const import (
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_TYPE,
    CONF_WEBHOOK_URL,
    DOMAIN,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)

SKI_AREA_PATH = "/serfaus-fiss-ladis/schneebericht/"
SKI_AREAS = {SKI_AREA_PATH: "Serfaus - Fiss - Ladis"}


@pytest.fixture(autouse=True)
def _never_really_set_up():
    """Keep a CREATE_ENTRY from setting the integration up for real.

    These tests are about the flow. Letting the created entry set up runs the
    whole integration: it builds Home Assistant's shared aiohttp session, whose
    aiodns resolver opens a c-ares channel and leaves that library's watchdog
    thread behind. pytest-socket cannot block it - c-ares resolves in C, below
    the Python sockets it patches - and the test harness then fails teardown
    over a thread no test can clean up.
    """
    with patch(
        "custom_components.bergfex.async_setup_entry",
        AsyncMock(return_value=True),
    ):
        yield


def _existing_entry(hass: HomeAssistant, ski_area: str) -> MockConfigEntry:
    """Register a resort that is already set up."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=ski_area.strip("/").split("/")[0],
        unique_id=ski_area,
        data={CONF_SKI_AREA: ski_area},
    )
    entry.add_to_hass(hass)
    return entry


async def _run_flow(hass: HomeAssistant, last_step: dict) -> dict:
    """Walk the whole flow, submitting `last_step` on the ski area form."""
    with patch(
        "custom_components.bergfex.config_flow.get_ski_areas",
        return_value=SKI_AREAS,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LANGUAGE: "at"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: TYPE_ALPINE}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "Österreich"}
        )
        return await hass.config_entries.flow.async_configure(
            result["flow_id"], last_step
        )


@pytest.mark.asyncio
async def test_flow_itself_sets_the_unique_id(
    hass: HomeAssistant, enable_custom_integrations
):
    """The flow has to assign the id, not the setup backfill.

    async_setup_entry backfills a missing id too, which would let this pass with
    the flow doing nothing - and the backfill only ever runs after the entry
    exists, so it cannot make the flow abort on a duplicate. Stub setup out, so
    the only thing that could have set the id is the flow.
    """
    with patch(
        "custom_components.bergfex.async_setup_entry",
        AsyncMock(return_value=True),
    ) as mock_setup:
        result = await _run_flow(hass, {CONF_SKI_AREA: SKI_AREA_PATH})
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert mock_setup.called
    assert result["result"].unique_id == SKI_AREA_PATH


@pytest.mark.asyncio
async def test_same_resort_twice_aborts(
    hass: HomeAssistant, enable_custom_integrations
):
    """A second entry for one resort duplicates every entity's unique id."""
    _existing_entry(hass, SKI_AREA_PATH)

    result = await _run_flow(hass, {CONF_SKI_AREA: SKI_AREA_PATH})

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_manual_path_is_normalized_before_the_unique_id(
    hass: HomeAssistant, enable_custom_integrations
):
    """A hand-typed path is completed to the same path, so it collides too."""
    _existing_entry(hass, SKI_AREA_PATH)

    result = await _run_flow(hass, {"manual_path": "serfaus-fiss-ladis"})

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_another_resort_is_still_added(
    hass: HomeAssistant, enable_custom_integrations
):
    """Only the same resort is refused - a different one goes through."""
    _existing_entry(hass, "/ischgl/schneebericht/")

    result = await _run_flow(hass, {CONF_SKI_AREA: SKI_AREA_PATH})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SKI_AREA] == SKI_AREA_PATH
    assert result["result"].unique_id == SKI_AREA_PATH


@pytest.mark.asyncio
async def test_pasted_url_is_reduced_to_the_path(
    hass: HomeAssistant, enable_custom_integrations
):
    """A pasted bergfex URL has to become the same path the list produces.

    Otherwise the host ends up inside the path, the unique id differs from the
    one the list would have built, the duplicate check misses it, and the entry
    points at a url that does not exist.
    """
    _existing_entry(hass, SKI_AREA_PATH)

    result = await _run_flow(
        hass,
        {"manual_path": "https://www.bergfex.at/serfaus-fiss-ladis/schneebericht/"},
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_pasted_url_for_a_new_resort_stores_the_bare_path(
    hass: HomeAssistant, enable_custom_integrations
):
    """The entry must store the path, never the pasted url."""
    result = await _run_flow(
        hass,
        {"manual_path": "https://www.bergfex.at/ischgl/"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SKI_AREA] == "/ischgl/schneebericht/"
    assert result["result"].unique_id == "/ischgl/schneebericht/"


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("serfaus-fiss-ladis", "/serfaus-fiss-ladis/schneebericht/"),
        ("/serfaus-fiss-ladis/schneebericht/", "/serfaus-fiss-ladis/schneebericht/"),
        (
            "https://www.bergfex.at/serfaus-fiss-ladis/schneebericht/",
            "/serfaus-fiss-ladis/schneebericht/",
        ),
        (
            "http://www.bergfex.it/serfaus-fiss-ladis/schneebericht/",
            "/serfaus-fiss-ladis/schneebericht/",
        ),
        (
            "  www.bergfex.at/serfaus-fiss-ladis/schneebericht/  ",
            "/serfaus-fiss-ladis/schneebericht/",
        ),
        (
            "https://www.bergfex.at/serfaus-fiss-ladis/",
            "/serfaus-fiss-ladis/schneebericht/",
        ),
    ],
)
def test_normalize_ski_area_path_alpine(typed: str, expected: str):
    """Every way a user can name a resort ends at one path."""
    assert normalize_ski_area_path(typed) == expected


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("seefeld", "/seefeld/"),
        ("https://www.bergfex.at/seefeld/langlaufen/", "/seefeld/langlaufen/"),
    ],
)
def test_normalize_ski_area_path_cross_country(typed: str, expected: str):
    """Cross country paths keep whatever subpage they name."""
    assert normalize_ski_area_path(typed, is_cross_country=True) == expected


ISCHGL_PATH = "/ischgl/schneebericht/"

# Every way a user can hand the flow one resort. They have to end at the exact
# path the picker produces, or the unique id differs and the duplicate check -
# the whole point of setting a unique id - never fires.
SAME_RESORT_INPUTS = [
    pytest.param(ISCHGL_PATH, id="already-normalized"),
    pytest.param("https://www.bergfex.at/ischgl/schneebericht", id="no-trailing-slash"),
    pytest.param("HTTPS://WWW.BERGFEX.AT/Ischgl/Schneebericht/", id="uppercase"),
    pytest.param("ischgl/schneebericht/?lang=de", id="query-string"),
    pytest.param("https://www.bergfex.at/ischgl/schneebericht/#schnee", id="fragment"),
    pytest.param("de.bergfex.at/ischgl/", id="schemeless-subdomain"),
]


@pytest.mark.parametrize("typed", SAME_RESORT_INPUTS)
@pytest.mark.asyncio
async def test_every_spelling_of_one_resort_is_refused_twice(
    hass: HomeAssistant, enable_custom_integrations, typed: str
):
    """Whatever the user pastes, an installed resort must be recognized.

    Copying a url without its trailing slash is routine, and so is a query
    string the address bar carries. Both used to be appended to the path
    verbatim: "/ischgl/schneebericht/schneebericht/" is a 404 and a different
    unique id, so the duplicate went straight through.
    """
    _existing_entry(hass, ISCHGL_PATH)

    result = await _run_flow(hass, {"manual_path": typed})

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("typed", SAME_RESORT_INPUTS)
@pytest.mark.asyncio
async def test_every_spelling_of_one_resort_stores_one_path(
    hass: HomeAssistant, enable_custom_integrations, typed: str
):
    """The stored path also has to be the one that exists on bergfex."""
    result = await _run_flow(hass, {"manual_path": typed})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SKI_AREA] == ISCHGL_PATH
    assert result["data"]["url"] == f"https://www.bergfex.at{ISCHGL_PATH}"
    assert result["result"].unique_id == ISCHGL_PATH


@pytest.mark.parametrize(
    "typed",
    ["bergfex.at", "/", "https://www.bergfex.at", "https://www.bergfex.at/?lang=de"],
)
@pytest.mark.asyncio
async def test_input_without_a_resort_is_rejected_on_the_form(
    hass: HomeAssistant, enable_custom_integrations, typed: str
):
    """Input that names no resort must come back as a form error.

    There is nothing to complete a bare domain into. It used to be turned into
    "//schneebericht/", whose name fallback then raised IndexError - which the
    user saw as "Unknown error occurred".
    """
    result = await _run_flow(hass, {"manual_path": typed})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "ski_area_list_alpine"
    assert result["errors"] == {"base": "invalid_path"}


@pytest.mark.asyncio
async def test_a_resort_without_a_subpage_still_gets_a_name(
    hass: HomeAssistant, enable_custom_integrations
):
    """A hand-entered resort is not in the list, so the path is its only name.

    A cross country path is just "/seefeld/": taking the second-to-last segment
    of it raises IndexError before the entry is ever created.
    """
    with patch(
        "custom_components.bergfex.config_flow.get_ski_areas",
        return_value={},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LANGUAGE: "at"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TYPE: TYPE_CROSS_COUNTRY}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "Österreich"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"manual_path": "seefeld"}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SKI_AREA] == "/seefeld/"
    assert result["data"]["name"] == "seefeld"
    assert result["title"] == "seefeld"


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("ischgl", "/ischgl/schneebericht/"),
        ("/ischgl/schneebericht/", "/ischgl/schneebericht/"),
        ("https://www.bergfex.at/ischgl/schneebericht", "/ischgl/schneebericht/"),
        ("HTTPS://WWW.BERGFEX.AT/Ischgl/Schneebericht/", "/ischgl/schneebericht/"),
        ("ischgl/schneebericht/?lang=de", "/ischgl/schneebericht/"),
        (
            "https://www.bergfex.at/ischgl/schneebericht/#schnee",
            "/ischgl/schneebericht/",
        ),
        ("de.bergfex.at/ischgl/", "/ischgl/schneebericht/"),
    ],
)
def test_normalize_folds_every_spelling_onto_one_path(typed: str, expected: str):
    """The helper's own view of the cases the flow tests drive."""
    assert normalize_ski_area_path(typed) == expected


@pytest.mark.parametrize(
    "typed", ["bergfex.at", "/", "https://www.bergfex.at", "www.bergfex.at/?lang=de"]
)
@pytest.mark.parametrize("is_cross_country", [False, True])
def test_normalize_rejects_input_without_a_resort(typed: str, is_cross_country: bool):
    """A bare domain names no resort, in either report type."""
    with pytest.raises(InvalidSkiAreaPath):
        normalize_ski_area_path(typed, is_cross_country=is_cross_country)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/ischgl/schneebericht/", "ischgl"),
        ("/seefeld/", "seefeld"),
        ("/venetien/langlaufen/cortina-ampezzo/loipen/", "cortina-ampezzo"),
    ],
)
def test_ski_area_name_from_path(path: str, expected: str):
    """The name falls back to the resort segment, never off the end of the list."""
    assert ski_area_name_from_path(path) == expected


@pytest.mark.parametrize(
    "typed",
    [
        "not a url",
        "example.com/hook",
        "ftp://example.com/hook",
        "file:///etc/passwd",
        "https://",
    ],
)
@pytest.mark.asyncio
async def test_a_webhook_that_is_not_a_url_is_rejected_on_the_form(
    hass: HomeAssistant, enable_custom_integrations, typed: str
):
    """The field is free text and every poll posts to whatever is in it.

    Unvalidated, a typo never surfaces in the flow where it could still be
    fixed - it surfaces as an error line in the log every few minutes, forever.
    """
    result = await _run_flow(hass, {CONF_SKI_AREA: SKI_AREA_PATH, "webhook_url": typed})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_webhook"}


@pytest.mark.asyncio
async def test_a_real_webhook_is_stored(
    hass: HomeAssistant, enable_custom_integrations
):
    """An http(s) url with a host is what the poll loop can actually post to."""
    result = await _run_flow(
        hass,
        {CONF_SKI_AREA: SKI_AREA_PATH, "webhook_url": " https://example.com/hook "},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    # Stripped, because a copied url routinely brings whitespace with it.
    assert result["data"][CONF_WEBHOOK_URL] == "https://example.com/hook"


@pytest.mark.asyncio
async def test_an_empty_webhook_is_stored_as_none(
    hass: HomeAssistant, enable_custom_integrations
):
    """An empty field means "no webhook", not a webhook that is the empty string."""
    result = await _run_flow(hass, {CONF_SKI_AREA: SKI_AREA_PATH, "webhook_url": ""})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_WEBHOOK_URL] is None


@pytest.mark.asyncio
async def test_choosing_nothing_reports_a_key_the_user_can_read(
    hass: HomeAssistant, enable_custom_integrations
):
    """The error key has to be the bare one.

    Home Assistant looks the message up under config.error.<key> itself, so
    "config.error.no_selection" asked it for
    config.error.config.error.no_selection - and the user was shown the raw key.
    """
    result = await _run_flow(hass, {})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_selection"}
