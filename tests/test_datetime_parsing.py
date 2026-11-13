"""Tests for the relative timestamps bergfex puts above the snow report."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.bergfex.parser import parse_bergfex_datetime

VIENNA = ZoneInfo("Europe/Vienna")


def _today():
    return datetime.now(VIENNA).date()


@pytest.mark.parametrize(
    ("lang", "printed"),
    [
        ("at", "Heute, 16:31"),
        ("en", "Today, 16:31"),
        ("fr", "Aujourd'hui, 16:31"),
        ("no", "I dag, 16:31"),
        ("hu", "Ma, 16:31"),
        ("ru", "Сегодня, 16:31"),
    ],
)
def test_today_in_every_shape_bergfex_prints_it(lang, printed):
    parsed = parse_bergfex_datetime(printed, lang)
    assert parsed.date() == _today()
    assert (parsed.hour, parsed.minute) == (16, 31)


def test_the_abbreviated_french_day_is_still_today():
    """bergfex serves the French page in two renderings and one shortens the word.

    Roughly one request in three returns "Auj." instead of "Aujourd'hui". Matched
    as a plain substring it yielded no timestamp at all, which took the card's
    "last updated" line away for that poll and failed the daily canary on three
    days out of five.
    """
    parsed = parse_bergfex_datetime("Auj., 16:31", "fr")
    assert parsed.date() == _today()
    assert (parsed.hour, parsed.minute) == (16, 31)


def test_yesterday_is_the_day_before():
    parsed = parse_bergfex_datetime("Gestern, 11:14", "at")
    assert parsed.date() == _today() - timedelta(days=1)
    assert (parsed.hour, parsed.minute) == (11, 14)


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        ("Fr, 28.11., 09:33", (11, 28, 9, 33)),
        ("Mo, 06.10., 07:00", (10, 6, 7, 0)),
    ],
)
def test_a_weekday_before_a_date_does_not_become_today(printed, expected):
    """The stem rule must not reach these.

    "Fr" and "Mo" are short words in front of a time as well, and accepting them
    would move the reading to today without anything looking wrong.
    """
    month, day, hour, minute = expected
    parsed = parse_bergfex_datetime(printed, "at")
    assert (parsed.month, parsed.day) == (month, day)
    assert (parsed.hour, parsed.minute) == (hour, minute)


def test_an_explicit_date_keeps_its_year():
    parsed = parse_bergfex_datetime("05.11.2025, 14:40", "at")
    assert parsed.date() == datetime(2025, 11, 5).date()


@pytest.mark.parametrize("printed", ["", "Auj.", "Gestern", "nonsense"])
def test_nothing_is_invented_without_a_time(printed):
    assert parse_bergfex_datetime(printed, "fr") is None


# Snippets copied from the live pages on 2026-11-13: the h2-sub line of the resort
# page (aichelberglifte, report of 4 Nov 11:02; hochkar, report of Wed 11 Nov 12:27).
_OLD_REPORT = {
    "at": "04.11.2026, 11:02",
    "en": "11/04/2026, 11:02",
    "fr": "04/11/2026, 11:02",
    "it": "04/11/2026, 11:02",
    "es": "04/11/26, 11:02",
    "nl": "04-11-26, 11:02",
    "dk": "04-11-2026, 11:02",
    "hu": "2026-11-04, 11:02",
    "se": "2026-11-04, 11:02",
}
_WEEKDAY_REPORT = {
    "at": "Mi, 11.11., 12:27",
    "en": "Wed, 11.11., 12:27",
    "fr": "Mer., 11.11., 12:27",
    "it": "Mer, 11.11., 12:27",
    "es": "Mié, 11.11., 12:27",
    "nl": "Wo, 11.11., 12:27",
    "dk": "Ons, 11.11., 12:27",
    "hu": "Sze, 11.11., 12:27",
    "se": "Ons, 11.11., 12:27",
}


@pytest.mark.parametrize(("lang", "printed"), sorted(_OLD_REPORT.items()))
def test_a_full_date_in_every_languages_own_shape(lang, printed):
    parsed = parse_bergfex_datetime(printed, lang)
    assert parsed is not None
    assert (parsed.year, parsed.month, parsed.day) == (2026, 11, 4)
    assert (parsed.hour, parsed.minute) == (11, 2)


@pytest.mark.parametrize(("lang", "printed"), sorted(_WEEKDAY_REPORT.items()))
def test_a_weekday_date_in_every_language(lang, printed):
    parsed = parse_bergfex_datetime(printed, lang)
    assert parsed is not None
    assert (parsed.month, parsed.day) == (11, 11)
    assert (parsed.hour, parsed.minute) == (12, 27)


def test_only_english_reads_the_month_first():
    assert parse_bergfex_datetime("11/04/2026, 11:02", "en").month == 11
    assert parse_bergfex_datetime("11/04/2026, 11:02", "fr").month == 4


def test_an_impossible_full_date_is_none():
    assert parse_bergfex_datetime("31/31/2026, 11:02", "fr") is None
