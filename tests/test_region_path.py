"""The region behind a resort, read off the breadcrumb.

Every region url the integration builds - the snow overview it takes "new snow"
from, and the six forecast image pages - is built from this one value, so a
wrong one fails six or seven requests per poll rather than one.
"""

from custom_components.bergfex.parser import parse_resort_page

PAGE = """
<html><body>
  <h1 class="text-4xl"><span>Skigebiet</span><span>Nebelhorn</span></h1>
  <ul aria-label="Breadcrumb">
    {crumbs}
  </ul>
</body></html>
"""

HOME = '<li><a href="/">bergfex</a></li>'
COUNTRY = '<li><a href="/deutschland/">Winter Deutschland</a></li>'
REGION = '<li><a href="/bayern/">Bayern</a></li>'
RESORT = '<li><a href="/nebelhorn-oberstdorf/">Skigebiet Nebelhorn</a></li>'

AREA = "/nebelhorn-oberstdorf/schneebericht/"


def _region(crumbs: str, area_path: str = AREA):
    return parse_resort_page(PAGE.format(crumbs=crumbs), area_path, "at").get(
        "region_path"
    )


def test_reads_the_region_from_a_full_breadcrumb():
    assert _region(HOME + COUNTRY + REGION + RESORT) == "/bayern/"


def test_steps_back_past_the_resort_on_a_subpage():
    """On /schneebericht/ the second-to-last crumb is the resort, not the region."""
    assert _region(COUNTRY + REGION + RESORT) == "/bayern/"


def test_a_breadcrumb_without_a_region_yields_none():
    """The reported bug.

    With only three crumbs the second-to-last is the resort and there is
    nothing behind it to step back to. The resort path was kept as the
    "region", and every url built from it 404s - a user's log carried
    "Could not fetch region snow report
    https://www.bergfex.at/nebelhorn-oberstdorf/schneewerte/" once per poll.
    """
    assert _region(HOME + RESORT + '<li><a href="/impressum/">x</a></li>') is None


def test_the_resort_is_never_its_own_region():
    """The invariant, stated directly: whatever else happens, not this."""
    for crumbs in (
        HOME + COUNTRY + REGION + RESORT,
        COUNTRY + REGION + RESORT,
        HOME + RESORT + '<li><a href="/impressum/">x</a></li>',
    ):
        region = _region(crumbs)
        assert region != "/nebelhorn-oberstdorf/"


def test_a_page_without_a_breadcrumb_yields_none():
    assert (
        parse_resort_page(
            "<html><body><h1>Nebelhorn</h1></body></html>", AREA, "at"
        ).get("region_path")
        is None
    )


def test_the_main_page_still_reads_its_region():
    """area_path is the resort itself there, so the prefix check must not fire
    against the region crumb."""
    assert _region(HOME + COUNTRY + REGION + RESORT, "/nebelhorn-oberstdorf/") == (
        "/bayern/"
    )
