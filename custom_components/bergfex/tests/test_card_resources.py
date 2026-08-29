"""Tests for the Lovelace card resource reconciliation."""

import pytest

from custom_components.bergfex import _is_bergfex_card_resource


@pytest.mark.parametrize(
    "url",
    [
        "/bergfex_frontend/bergfex-card.js",
        "/bergfex_frontend/bergfex-card.js?v=3.0.0",
        "/hacsfiles/lovelace-bergfex-card/bergfex-card.js",
        "/hacsfiles/lovelace-bergfex-card/bergfex-card.js?hacstag=123",
        "/local/bergfex-card.js",
        "/local/community/lovelace-bergfex-card/bergfex-card.js?v=2.2.1",
    ],
)
def test_detects_every_bergfex_card_resource(url):
    """Any resource loading a bergfex-card.js bundle must be recognised."""
    assert _is_bergfex_card_resource(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "/hacsfiles/other-card/other-card.js",
        "/local/my-bergfex-card-fork.js",
        "/hacsfiles/bergfex-weather/bergfex-weather-card.js",
        "/bergfex_frontend/some-other-file.js",
        "",
    ],
)
def test_leaves_unrelated_resources_alone(url):
    """Deleting somebody else's resource would be far worse than a leftover."""
    assert _is_bergfex_card_resource(url) is False
