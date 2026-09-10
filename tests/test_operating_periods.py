"""Tests for the winter/summer operating periods.

bergfex shows both periods in one panel. The headline "Saison" field carries
whichever season is current, so in August a ski resort reports a summer period -
which is why these are read structurally instead.
"""

from datetime import date

from custom_components.bergfex.parser import parse_resort_page

PANEL = """
<html><body>
  <h1 class="text-4xl"><span>Skigebiet</span><span>Warth / Schröcken</span></h1>
  <div class="pt-6">
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><div class="txt_markup"><p>05.12.2025 - 12.04.2026</p></div>
      <h3>Betrieb</h3><div class="txt_markup"><p>09:00 - 16:15</p></div>
    </div>
    <div class="block" x-show="tab == 'summer'">
      <h3>Saison</h3><div class="txt_markup"><p>19.06.2026 - 11.10.2026</p></div>
    </div>
  </div>
</body></html>
"""


def test_reads_the_winter_period():
    data = parse_resort_page(PANEL, "at")
    assert data["winter_season_start"] == date(2025, 12, 5)
    assert data["winter_season_end"] == date(2026, 4, 12)


def test_reads_the_summer_period_separately():
    data = parse_resort_page(PANEL, "at")
    assert data["summer_season_start"] == date(2026, 6, 19)
    assert data["summer_season_end"] == date(2026, 10, 11)


def test_does_not_confuse_the_two_periods():
    """The whole point: in August the headline season is the summer one."""
    data = parse_resort_page(PANEL, "at")
    assert data["winter_season_start"] != data["summer_season_start"]


def test_works_regardless_of_label_language():
    """The x-show expression is identical across bergfex's domains, the labels are not."""
    english = PANEL.replace("Saison", "Season").replace("Betrieb", "Operation")
    data = parse_resort_page(english, "en")
    assert data["winter_season_start"] == date(2025, 12, 5)


def test_tolerates_a_page_without_the_panel():
    """Subpages such as /schneebericht/ do not carry it."""
    data = parse_resort_page("<html><body><h1>Warth</h1></body></html>", "at")
    assert "winter_season_start" not in data
    assert "summer_season_start" not in data


def test_tolerates_a_panel_without_parsable_dates():
    broken = PANEL.replace("05.12.2025 - 12.04.2026", "auf Anfrage")
    data = parse_resort_page(broken, "at")
    assert "winter_season_start" not in data
    # the summer block is independent and must still come through
    assert data["summer_season_start"] == date(2026, 6, 19)


def test_accepts_slash_separated_dates():
    slashes = PANEL.replace("05.12.2025 - 12.04.2026", "05/12/2025 - 12/04/2026")
    data = parse_resort_page(slashes, "at")
    assert data["winter_season_start"] == date(2025, 12, 5)


def test_accepts_en_dash_between_dates():
    dashed = PANEL.replace("05.12.2025 - 12.04.2026", "05.12.2025 – 12.04.2026")
    data = parse_resort_page(dashed, "at")
    assert data["winter_season_end"] == date(2026, 4, 12)


HOURS_DD = """
<html><body>
  <dl>
    <dt>Orario</dt>
    <dd>{hours}</dd>
  </dl>
</body></html>
"""


def test_reads_an_hour_without_a_leading_zero():
    """bergfex prints "8:30", not "08:30", on the Italian pages.

    The regex demanded two digits for the hour, so the whole opening time was
    dropped - silently, because the operation_status text next to it still
    parsed. See the bare "8:30 - 16:00" in tests/fixtures/airolo.html.
    """
    data = parse_resort_page(HOURS_DD.format(hours="8:30 - 16:00"), "/airolo/", "it")

    assert data["operating_hours_start"] == "08:30"
    assert data["operating_hours_end"] == "16:00"


def test_reads_hours_separated_by_an_en_dash():
    """The season panel already accepted a dash; this field did not."""
    data = parse_resort_page(HOURS_DD.format(hours="09:00 – 16:45"), "/airolo/", "it")

    assert data["operating_hours_start"] == "09:00"
    assert data["operating_hours_end"] == "16:45"


def test_a_padded_hour_still_reads():
    data = parse_resort_page(HOURS_DD.format(hours="09:00 - 16:45"), "/airolo/", "it")

    assert data["operating_hours_start"] == "09:00"
    assert data["operating_hours_end"] == "16:45"


def test_pads_a_bare_hour_so_two_resorts_agree():
    """"8:30" and "09:00" in one card looked like two different formats."""
    data = parse_resort_page(HOURS_DD.format(hours="8:30 - 9:05"), "/airolo/", "it")

    assert data["operating_hours_start"] == "08:30"
    assert data["operating_hours_end"] == "09:05"


def test_pads_the_season_panel_hours_too():
    panel = PANEL.replace("09:00 - 16:15", "8:30 - 9:05")
    data = parse_resort_page(panel, "at")

    assert data["winter_operating_hours_start"] == "08:30"
    assert data["winter_operating_hours_end"] == "09:05"


def test_bare_opening_times_are_not_an_operation_status():
    """The Italian pages print only the times under the hours label.

    Putting them into operation_status made the field read "08:30 - 16:00"
    where the card expects a word such as "täglich".
    """
    data = parse_resort_page(HOURS_DD.format(hours="8:30 - 16:00"), "/airolo/", "it")

    assert "operation_status" not in data


def test_a_status_word_next_to_the_times_still_becomes_the_status():
    data = parse_resort_page(
        HOURS_DD.format(hours="täglich 08:30 - 16:00"), "/airolo/", "it"
    )

    assert data["operation_status"] == "täglich"
    assert data["operating_hours_start"] == "08:30"


def test_a_status_word_without_times_is_unchanged():
    data = parse_resort_page(HOURS_DD.format(hours="täglich"), "/airolo/", "it")

    assert data["operation_status"] == "täglich"
    assert "operating_hours_start" not in data
