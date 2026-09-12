"""Unique id schemes for Bergfex entities.

Kept in one module because the collision this fixes came from three places
inventing their own scheme: sensor.py, image.py's constructor, and image.py
again at runtime. The platforms and the registry migration in __init__.py now
all build their strings here.
"""

from __future__ import annotations

from homeassistant.util import slugify


def unique_id_prefix(area_path: str) -> str:
    """Return the unique id prefix for a resort.

    Keyed on the resort path rather than the display name. A display name is not
    unique - bergfex happily lists two resorts as "Bergbahnen" - and slugifying
    it handed both of them the same ids, so Home Assistant refused the second
    resort's entities outright. The path is what the config flow already treats
    as the entry's identity, so both namespaces now agree and its duplicate
    check finally covers the entities too.

    The path is used verbatim rather than slugified: slugify folds the
    separators away, so "/a-b/" and "/a/b/" would land on the same prefix and
    reintroduce the very collision this exists to remove.
    """
    return f"bergfex_{area_path.strip('/')}_"


def build_unique_id(area_path: str, key: str) -> str:
    """Return the unique id for one of a resort's entities."""
    return f"{unique_id_prefix(area_path)}{key}"


def legacy_unique_id_prefixes(area_name: str) -> tuple[str, ...]:
    """Return the name-based prefixes entities were registered under before.

    Two of them, because the platforms disagreed. sensor.py slugified the
    display name; image.py built the same slug in its constructor but then
    overwrote the id at runtime with a lower-and-underscore variant that keeps
    the characters slugify drops. A resort named "Feldberg / Hochschwarzwald"
    therefore had its sensors under "bergfex_feldberg_hochschwarzwald_" and its
    images under "bergfex_feldberg_/_hochschwarzwald_".

    Both have to be migrated or those entities are orphaned, which costs the
    user their history, customisations and every dashboard reference.
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
    """Return the key a resort's coordinator is stored under.

    The store used to be keyed on the display name. Two resorts sharing a name
    therefore shared one coordinator, and since a coordinator only ever fetches
    the path it was built for, the second resort silently reported the first
    one's snow. The path is per-entry unique, so it cannot alias.
    """
    return f"bergfex_{area_path.strip('/')}"
