"""Tests for the Lovelace card resource reconciliation."""

import pytest

from custom_components.bergfex import (
    CARD_FILENAME,
    CARD_URL_BASE,
    _async_reconcile_card_resource,
    _is_bergfex_card_resource,
)

NEW_URL = f"{CARD_URL_BASE}/{CARD_FILENAME}?v=3.1.0"


class FakeResources:
    """Stand-in for Home Assistant's ResourceStorageCollection.

    The real collection is loaded lazily: async_items() stays empty until a
    write - or an explicit load - pulls the stored items in.
    """

    def __init__(self, stored=None):
        self._stored = [dict(item) for item in stored or []]
        self._items = []
        self._next_id = len(self._stored)
        self.loaded = False

    async def _async_ensure_loaded(self):
        if not self.loaded:
            await self.async_load()

    async def async_load(self):
        self._items = [dict(item) for item in self._stored]
        self.loaded = True

    def async_items(self):
        return self._items

    async def async_create_item(self, data):
        await self._async_ensure_loaded()
        item = {"id": f"generated{self._next_id}", **data}
        self._next_id += 1
        self._items.append(item)
        return item

    async def async_update_item(self, item_id, updates):
        await self._async_ensure_loaded()
        item = next(item for item in self._items if item["id"] == item_id)
        item.update(updates)
        return item

    async def async_delete_item(self, item_id):
        await self._async_ensure_loaded()
        self._items = [item for item in self._items if item["id"] != item_id]


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


async def test_registers_the_card_on_a_fresh_install():
    """Without a resource for our bundle, exactly one is created."""
    resources = FakeResources()

    removed = await _async_reconcile_card_resource(resources, NEW_URL)

    assert [item["url"] for item in resources.async_items()] == [NEW_URL]
    assert removed == []


async def test_does_not_add_a_second_resource_on_restart():
    """Regression: the store is empty until loaded, so our own entry was missed.

    Every restart appended another resource, and the browser then loaded the
    bundle twice.
    """
    resources = FakeResources(
        [
            {
                "id": "existing",
                "res_type": "module",
                "url": f"{CARD_URL_BASE}/{CARD_FILENAME}?v=3.0.0",
            }
        ]
    )

    await _async_reconcile_card_resource(resources, NEW_URL)

    assert [item["url"] for item in resources.async_items()] == [NEW_URL]
    assert resources.async_items()[0]["id"] == "existing"


async def test_removes_duplicates_and_reports_the_standalone_card():
    """Duplicates go, and the HACS leftover is reported so the issue can be raised."""
    hacs_url = "/hacsfiles/lovelace-bergfex-card/bergfex-card.js"
    resources = FakeResources(
        [
            {
                "id": "one",
                "res_type": "module",
                "url": f"{CARD_URL_BASE}/{CARD_FILENAME}?v=3.0.0",
            },
            {
                "id": "two",
                "res_type": "module",
                "url": f"{CARD_URL_BASE}/{CARD_FILENAME}?v=2.9.0",
            },
            {"id": "hacs", "res_type": "module", "url": hacs_url},
            {
                "id": "other",
                "res_type": "module",
                "url": "/hacsfiles/other-card/other-card.js",
            },
        ]
    )

    removed = await _async_reconcile_card_resource(resources, NEW_URL)

    assert sorted(item["url"] for item in resources.async_items()) == sorted(
        [NEW_URL, "/hacsfiles/other-card/other-card.js"]
    )
    assert hacs_url in removed


class UnknownCollection:
    """A resource collection we cannot recognise: no flag, no way to load it.

    Reconciling against this would mean reading an empty item list and writing a
    store that no longer holds any other card's resource.
    """

    def __init__(self):
        self.created = []

    def async_items(self):
        return []

    async def async_create_item(self, data):
        self.created.append(data)
        return data


async def test_refuses_to_register_against_a_collection_it_cannot_load():
    """Better no resource than a store with every other card's dropped."""
    resources = UnknownCollection()

    with pytest.raises(AttributeError):
        await _async_reconcile_card_resource(resources, NEW_URL)

    assert resources.created == []


async def test_does_not_register_when_the_store_cannot_be_loaded():
    """A failed load must abort, not fall through to creating a resource."""

    class UnloadableResources(FakeResources):
        async def async_load(self):
            raise RuntimeError("storage unavailable")

    resources = UnloadableResources(
        [
            {
                "id": "other",
                "res_type": "module",
                "url": "/hacsfiles/other-card/other-card.js",
            }
        ]
    )

    with pytest.raises(RuntimeError):
        await _async_reconcile_card_resource(resources, NEW_URL)

    assert resources.async_items() == []
