"""Shared fixtures for the whole suite."""

import pytest

import custom_components.bergfex.coordinator as bergfex_coordinator


@pytest.fixture(autouse=True)
def _no_shared_pages_between_tests():
    """The shared page caches are module state, and live for minutes to hours.

    A test that reads a region page must not be served the one an earlier test
    left behind - two tests of the same region would otherwise depend on the
    order they run in.
    """
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()
    yield
    bergfex_coordinator._FORECAST_CACHE.clear()
    bergfex_coordinator._REGION_PAGE_CACHE.clear()
