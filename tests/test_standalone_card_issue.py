"""The "uninstall the standalone card" repair has to go away when you do.

Reported against a real 3.0.0 install: the user opened HACS, uninstalled the
Bergfex Card exactly as the repair asked, restarted - and the warning was still
there. It was raised on the single run that removed the stale Lovelace resource
and never looked at again, and it is persistent, so nothing could ever take it
away. Complying with it was indistinguishable from ignoring it.
"""

from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import flush_store

from custom_components.bergfex.__init__ import (
    CARD_FILENAME,
    LEGACY_CARD_ISSUE_ID,
    _async_report_standalone_card,
    _standalone_card_files,
)
from custom_components.bergfex.const import DOMAIN


@pytest.fixture(autouse=True)
def isolated_config_dir(hass: HomeAssistant, tmp_path: Path):
    """Give each test its own config directory.

    The shared one these tests would otherwise write into lives inside
    site-packages and is reused by every test in the run, so a card "installed"
    by one test is still installed for the next.
    """
    hass.config.config_dir = str(tmp_path)
    return tmp_path


def _install_hacs_card(config_dir: str, repo: str = "lovelace-bergfex-card") -> Path:
    """Put the card where HACS unpacks a frontend plugin."""
    path = Path(config_dir) / "www" / "community" / repo / CARD_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("/* the standalone card */", encoding="utf-8")
    return path


def _issue(hass: HomeAssistant):
    return ir.async_get(hass).async_get_issue(DOMAIN, LEGACY_CARD_ISSUE_ID)


class TestDetection:
    def test_finds_the_hacs_copy(self, hass: HomeAssistant):
        _install_hacs_card(hass.config.config_dir)

        assert len(_standalone_card_files(hass.config.config_dir)) == 1

    def test_finds_it_under_the_renamed_repository_too(self, hass: HomeAssistant):
        """The repository was renamed, so both directory names are in the wild."""
        _install_hacs_card(hass.config.config_dir, repo="bergfex-card")

        assert len(_standalone_card_files(hass.config.config_dir)) == 1

    def test_a_config_without_a_www_directory_is_not_an_installation(
        self, hass: HomeAssistant
    ):
        assert _standalone_card_files(hass.config.config_dir) == []

    def test_a_hand_placed_local_copy_is_not_a_hacs_installation(
        self, hass: HomeAssistant
    ):
        """`/local/bergfex-card.js` is www/, not www/community/.

        Its resource is still removed - it just cannot be uninstalled through
        HACS, so telling the user to open HACS would send them nowhere.
        """
        local = Path(hass.config.config_dir) / "www" / CARD_FILENAME
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text("/* hand placed */", encoding="utf-8")

        assert _standalone_card_files(hass.config.config_dir) == []


class TestTheRepair:
    async def test_raised_while_the_files_are_there(self, hass: HomeAssistant):
        _install_hacs_card(hass.config.config_dir)

        await _async_report_standalone_card(hass)

        assert _issue(hass) is not None

    async def test_not_raised_when_they_are_not(self, hass: HomeAssistant):
        await _async_report_standalone_card(hass)

        assert _issue(hass) is None

    async def test_uninstalling_and_restarting_clears_it(self, hass: HomeAssistant):
        """The reported bug, start to finish.

        Raise it the way an upgrade does, uninstall through HACS, start again.
        Before this fix the second report was never reached at all, and even
        reaching it would have left the issue standing.
        """
        card = _install_hacs_card(hass.config.config_dir)
        await _async_report_standalone_card(hass)
        assert _issue(hass) is not None

        card.unlink()
        card.parent.rmdir()
        await _async_report_standalone_card(hass)

        assert _issue(hass) is None

    async def test_it_survives_a_restart_while_the_card_is_still_installed(
        self, hass: HomeAssistant
    ):
        """Clearing itself must not turn into vanishing before it is acted on."""
        _install_hacs_card(hass.config.config_dir)
        await _async_report_standalone_card(hass)

        registry = ir.async_get(hass)
        await flush_store(registry._store)
        reloaded = ir.IssueRegistry(hass)
        await reloaded.async_load()

        issue = reloaded.async_get_issue(DOMAIN, LEGACY_CARD_ISSUE_ID)
        assert issue is not None
        assert issue.active

    async def test_re_raising_it_every_start_is_harmless(self, hass: HomeAssistant):
        _install_hacs_card(hass.config.config_dir)

        for _ in range(3):
            await _async_report_standalone_card(hass)

        assert _issue(hass) is not None
        assert len(ir.async_get(hass).issues) == 1
