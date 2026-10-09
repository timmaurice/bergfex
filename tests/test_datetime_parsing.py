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
