"""What the integration declares about itself, and what it lets users delete."""

import json
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.__init__ import async_remove_config_entry_device
from custom_components.bergfex.const import DOMAIN

ROOT = Path(__file__).resolve().parent.parent
AREA_PATH = "/it/test/schneebericht/"


def test_manifest_declares_the_lovelace_dependency():
    """__init__.py reads hass.data["lovelace"] to register the card resource.

    Without after_dependencies Home Assistant may set us up before lovelace is
    there, and the card silently never gets registered.
    """
    manifest = json.loads(
        (ROOT / "custom_components" / "bergfex" / "manifest.json").read_text()
    )

    assert "lovelace" in manifest.get("after_dependencies", [])


def test_hacs_declares_a_minimum_home_assistant_version():
    """async_register_static_paths does not exist before 2024.7."""
    hacs = json.loads((ROOT / "hacs.json").read_text())

    minimum = hacs.get("homeassistant")
    assert minimum, "HACS would otherwise offer the integration to any version"

    major, minor = (int(part) for part in minimum.split(".")[:2])
    assert (major, minor) >= (2024, 7)


TRANSLATIONS = ROOT / "custom_components" / "bergfex" / "translations"


@pytest.mark.parametrize(
    "path", sorted(TRANSLATIONS.glob("*.json")), ids=lambda path: path.name
)
def test_a_repair_issue_carries_a_description_or_a_fix_flow(path: Path):
    """hassfest rejects an issue that carries both, and CI runs hassfest.

    A repair issue either explains itself and leaves the user to act (title plus
    description) or hands them a repair flow (title plus fix_flow). Carrying both
    is the one shape hassfest refuses - vol.Exclusive on the "fixable" group -
    and it fails the whole integration, not just the file.
    """
    issues = json.loads(path.read_text(encoding="utf-8")).get("issues", {})
    assert issues, f"{path.name} declares no issues"

    for key, issue in issues.items():
        where = f"{path.name}:{key}"
        assert issue.get("title"), f"{where} has no title"
        assert ("description" in issue) != ("fix_flow" in issue), (
            f"{where} must carry exactly one of description/fix_flow"
        )


def test_every_language_declares_the_same_repair_issues():
    """A missing key falls back to English, a stray one is dead weight."""
    reference = json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8"))
    expected = {
        key: sorted(issue) for key, issue in reference.get("issues", {}).items()
    }

    for path in sorted(TRANSLATIONS.glob("*.json")):
        issues = json.loads(path.read_text(encoding="utf-8")).get("issues", {})
        assert {
            key: sorted(issue) for key, issue in issues.items()
        } == expected, f"{path.name} does not match en.json"


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
            "ski_area": AREA_PATH,
            "language": "it",
            "type": "alpine",
        },
        source="user",
        entry_id="test_entry_id",
    )


def _device(hass, entry, identifier) -> dr.DeviceEntry:
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, identifier)},
    )


@pytest.mark.asyncio
async def test_a_stale_device_can_be_deleted(hass: HomeAssistant, mock_config_entry):
    """A resort the entry no longer serves is the case the hook exists for."""
    mock_config_entry.add_to_hass(hass)
    stale = _device(hass, mock_config_entry, "/it/moved-away/schneebericht/")

    assert await async_remove_config_entry_device(hass, mock_config_entry, stale)


@pytest.mark.asyncio
async def test_the_live_device_cannot_be_deleted(hass: HomeAssistant, mock_config_entry):
    """Deleting it would only have it recreated, minus the user's settings."""
    mock_config_entry.add_to_hass(hass)
    live = _device(hass, mock_config_entry, AREA_PATH)

    assert not await async_remove_config_entry_device(hass, mock_config_entry, live)


@pytest.mark.asyncio
async def test_an_entry_without_a_ski_area_deletes_nothing(
    hass: HomeAssistant, mock_config_entry
):
    """A missing ski_area would make `area_path` None, which matches nothing.

    Every identifier would then compare unequal and the hook would report the
    live device as deletable too, taking the user's area assignment, custom name
    and dashboard references with it.
    """
    entry = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Resort",
        data={"name": "Test Resort", "language": "it", "type": "alpine"},
        source="user",
        entry_id="no_area_entry",
    )
    entry.add_to_hass(hass)
    live = _device(hass, entry, AREA_PATH)

    assert not await async_remove_config_entry_device(hass, entry, live)
