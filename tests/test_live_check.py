"""Tests for the daily live-site canary.

The point of these is narrow but important: before this, every one of the
script's failure paths exited 0. The scheduled run reported success while the
snow-report block was entirely missing from bergfex.
"""

import datetime
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_live_site as clc  # noqa: E402


def mismatch(key="lifts"):
    return {
        "kind": "mismatch",
        "key": key,
        "at": "lifte",
        "expected": "lifts",
        "found": "Something else",
    }


def absent(key):
    return {"kind": "absent", "key": key, "detail": "selector matched nothing"}


def run(results, gaps=frozenset(), *, winter):
    """Run report() and return its exit code, 0 meaning it did not call sys.exit."""
    os.environ["BERGFEX_FORCE_SEASON"] = "1" if winter else "0"
    try:
        clc.report(results, set(gaps))
    except SystemExit as exc:
        return exc.code
    finally:
        del os.environ["BERGFEX_FORCE_SEASON"]
    return 0


class TestSeasonality:
    def test_snow_report_keys_are_seasonal(self):
        for key in ("mountain", "valley", "snow_condition", "lifts", "classical"):
            assert clc.key_is_seasonal(key) is True

    def test_main_page_keys_are_published_year_round(self):
        for key in ("season", "prices", "operating_hours", "day_ticket"):
            assert clc.key_is_seasonal(key) is False

    def test_summer_is_off_season_and_midwinter_is_not(self):
        assert clc.in_season(datetime.date(2026, 8, 30)) is False
        assert clc.in_season(datetime.date(2026, 1, 15)) is True

    @pytest.mark.parametrize("month", [9, 10, 11, 4, 5])
    def test_shoulder_months_do_not_demand_a_snow_report(self, month):
        """Only the glaciers report in October and November.

        Demanding a snow report then would fail every autumn, and a canary that
        cries wolf gets muted. Restructures in these months are still caught by
        the year-round keys.
        """
        assert clc.in_season(datetime.date(2026, month, 15)) is False

    @pytest.mark.parametrize("month", [12, 1, 2, 3])
    def test_core_winter_demands_a_snow_report(self, month):
        assert clc.in_season(datetime.date(2027 if month == 12 else 2026, month, 15)) is True

    def test_the_calendar_can_be_overridden(self):
        os.environ["BERGFEX_FORCE_SEASON"] = "1"
        try:
            assert clc.in_season(datetime.date(2026, 8, 30)) is True
        finally:
            del os.environ["BERGFEX_FORCE_SEASON"]


class TestVerdict:
    def test_clean_run_passes(self):
        assert run([("de", [], [])], winter=True) == 0

    def test_keyword_mismatch_always_fails(self):
        assert run([("de", [mismatch()], [])], winter=False) == 1

    def test_missing_snow_report_is_tolerated_off_season(self):
        """The case that must not cry wolf: bergfex drops this block every summer."""
        assert run([("de", [absent("mountain")], [])], winter=False) == 0

    def test_missing_snow_report_fails_during_the_season(self):
        assert run([("de", [absent("mountain")], [])], winter=True) == 1

    @pytest.mark.parametrize("key", ["season", "prices", "operating_hours"])
    def test_missing_year_round_structure_fails_even_off_season(self, key):
        """These are published in summer too, so absence means a restructure."""
        assert run([("de", [absent(key)], [])], winter=False) == 1

    def test_baseline_gaps_are_judged_like_absences(self):
        """A key missing from the baseline is skipped for all 18 languages."""
        assert run([("de", [], [])], gaps={"season"}, winter=False) == 1
        assert run([("de", [], [])], gaps={"mountain"}, winter=False) == 0
        assert run([("de", [], [])], gaps={"mountain"}, winter=True) == 1


class TestOutput:
    def test_does_not_claim_success_when_the_structure_is_absent(self, capsys):
        run([("de", [absent("mountain")], [])], winter=False)
        out = capsys.readouterr().out
        assert "could not be verified" in out
        assert "Validation successful" not in out

    def test_claims_success_only_when_everything_was_found(self, capsys):
        run([("de", [], [])], winter=False)
        assert "Validation successful" in capsys.readouterr().out

    def test_names_the_reason_a_year_round_key_is_critical(self, capsys):
        run([("de", [absent("season")], [])], winter=False)
        out = capsys.readouterr().out
        assert "restructured" in out
        assert "'season'" in out or "season" in out
