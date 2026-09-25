"""Unique id schemes for Bergfex entities.

Kept in one module because the collision this fixes came from three places
inventing their own scheme. The platforms and the registry migration in
__init__.py all build their strings here.
"""

from __future__ import annotations

from homeassistant.util import slugify


def unique_id_prefix(area_path: str) -> str:
    """Return the unique id prefix for a resort.

    Keyed on the resort path, not the display name: bergfex lists more than one
    resort as "Bergbahnen", and slugifying gave both the same ids. The path is
    what the config flow treats as the entry's identity, so both namespaces agree.

    Used verbatim rather than slugified - slugify folds separators away, so
    "/a-b/" and "/a/b/" would collide again.
    """
    return f"bergfex_{area_path.strip('/')}_"


def build_unique_id(area_path: str, key: str) -> str:
    """Return the unique id for one of a resort's entities."""
    return f"{unique_id_prefix(area_path)}{key}"


def legacy_unique_id_prefixes(area_name: str) -> tuple[str, ...]:
    """Return the name-based prefixes entities were registered under before.

    Two of them, because the platforms disagreed: sensor.py slugified the display
    name, image.py overwrote the id at runtime with a variant that keeps the
    characters slugify drops. "Feldberg / Hochschwarzwald" therefore had sensors
    under "bergfex_feldberg_hochschwarzwald_" and images under
    "bergfex_feldberg_/_hochschwarzwald_". Both must migrate or those entities
    are orphaned, costing the user history and dashboard references.
    """
    # dict.fromkeys keeps the order and drops the duplicate for the common case
    # where a name has nothing in it that the two schemes disagree about.
    return tuple(
        dict.fromkeys(
            (
                f"bergfex_{slugify(area_name)}_",
                f"bergfex_{area_name.lower().replace(' ', '_')}_",
            )
        )
    )


def coordinator_key(area_path: str) -> str:
    """Return the name of a resort's coordinator.

    Built from the path, which is per-entry unique. Coordinators used to be
    stored under this key, and on the display name two resorts sharing a name
    shared one coordinator - and a coordinator only ever fetches the path it was
    built for, so the second reported the first's snow. Each entry now keeps its
    own in runtime_data; the name only labels it in the log.
    """
    return f"bergfex_{area_path.strip('/')}"
