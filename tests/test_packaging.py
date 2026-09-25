"""What the integration declares about itself, and what it lets users delete."""

import json
import re
from pathlib import Path

import pytest
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from packaging.version import Version
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.__init__ import async_remove_config_entry_device
from custom_components.bergfex.const import DOMAIN
from custom_components.bergfex.sensor import ALPINE_SENSORS, CROSS_COUNTRY_SENSORS

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
    """The declared minimum is the core CI actually validates.

    This is a support decision, not only a technical floor. The technical floor
    is lower: 2024.12 for `OptionsFlowHandler` reading `self.config_entry`, and
    2025.2 before that for `hass.data["lovelace"]` being an object rather than a
    plain dict - below which the bundled card silently never registers itself.
    Since CI resolves and exercises only the current core, declaring anything
    older would promise support nobody verifies.
    """
    hacs = json.loads((ROOT / "hacs.json").read_text())

    minimum = hacs.get("homeassistant")
    assert minimum, "HACS would otherwise offer the integration to any version"

    major, minor = (int(part) for part in minimum.split(".")[:2])
    assert (major, minor) >= (2026, 9)


def test_hacs_does_not_offer_a_core_ci_never_accepts():
    """HACS would otherwise install on cores older than any CI run could have used.

    MINIMUM_CORE in tests.yml is the oldest core a test run is allowed to
    resolve. A hacs.json minimum below it promises support for cores the suite
    never sees, which is how 2026.9.0 stayed declared while CI floored at 2026.9.1.
    """
    hacs = json.loads((ROOT / "hacs.json").read_text())
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "tests.yml").read_text()
    )

    assert Version(hacs["homeassistant"]) >= Version(workflow["env"]["MINIMUM_CORE"])


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
        assert ("description" in issue) != (
            "fix_flow" in issue
        ), f"{where} must carry exactly one of description/fix_flow"


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


ICONS = ROOT / "custom_components" / "bergfex" / "icons.json"


def test_every_sensor_has_an_icon():
    """Without one the frontend falls back to the generic sensor icon."""
    icons = json.loads(ICONS.read_text(encoding="utf-8"))["entity"]["sensor"]

    for description in (*ALPINE_SENSORS, *CROSS_COUNTRY_SENSORS):
        assert (
            description.icon or description.translation_key in icons
        ), f"{description.key} has no icon"


def test_icons_json_has_the_shape_hassfest_accepts():
    """A key no entity translates is a typo the frontend silently ignores."""
    icons = json.loads(ICONS.read_text(encoding="utf-8"))
    names = json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8"))

    assert set(icons) == {"entity"}
    for platform, entries in icons["entity"].items():
        for key, icon in entries.items():
            where = f"{platform}.{key}"
            assert key in names["entity"].get(platform, {}), f"{where} is unknown"
            assert set(icon) == {"default"}, f"{where} carries more than a default"
            assert re.fullmatch(r"mdi:[a-z0-9-]+", icon["default"]), where


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
async def test_the_live_device_cannot_be_deleted(
    hass: HomeAssistant, mock_config_entry
):
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


def test_the_manifest_pins_what_requirements_txt_pins():
    """manifest.json is what Home Assistant installs; requirements.txt is not.

    The two drifted once already, and in the direction that matters: the
    CHANGELOG recorded lxml being raised to >=6.1.1 for CVE-2026-41066, but only
    requirements.txt moved. Users kept installing >=6.1.0, so a security fix that
    was written down had never actually shipped.
    """
    manifest = json.loads(
        (ROOT / "custom_components" / "bergfex" / "manifest.json").read_text()
    )
    declared = dict(requirement.split(">=") for requirement in manifest["requirements"])

    pinned = dict(
        line.split(">=")
        for line in (ROOT / "requirements.txt").read_text().split()
        if ">=" in line
    )

    assert declared == pinned
