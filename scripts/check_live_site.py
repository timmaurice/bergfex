#!/usr/bin/env python3
"""
Global Baseline Structural Validation Script for Bergfex (Harden Version).
Uses strict exact-matching for baseline mapping and prevents misidentification
of keywords from large containers.
"""

import sys
import os
import asyncio
import datetime
import random
import re
import aiohttp
from bs4 import BeautifulSoup
from unittest.mock import MagicMock

# This script runs in CI without Home Assistant installed. Stub it out only when
# it is genuinely missing - unconditional stubbing would poison sys.modules for
# anything that imports this module afterwards, the test suite included.
try:  # pragma: no cover - depends on the environment, not on the code
    import homeassistant  # noqa: F401
except ImportError:  # pragma: no cover
    for _name in (
        "homeassistant",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.aiohttp_client",
        "homeassistant.helpers.update_coordinator",
        "homeassistant.exceptions",
    ):
        sys.modules[_name] = MagicMock()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from custom_components.bergfex.const import SUPPORTED_LANGUAGES, KEYWORDS

# Configuration of structural groups
GROUPS = {
    "snow_big": {
        "page": "snow",
        "selector": "dt.big",
        "keys": ["mountain", "valley", "snow_depth"],
        "strict": False,  # because it has elevations like (1.377m)
    },
    "snow_standard": {
        "page": "snow",
        "selector": "dt:not(.big), th",
        "keys": [
            "snow_condition",
            "last_snowfall",
            "avalanche",
            "operation",
            "lifts",
            "pistes",
            "slope_condition",
        ],
        "strict": False,  # because it often has trailing 'Region'
    },
    "main_labels": {
        "page": "main",
        # bergfex dropped the Tailwind `tw-` class prefix at some point; both are
        # matched so the check keeps working across the change.
        "selector": (
            "span.tw-font-semibold, span.font-semibold, div.box-header, "
            "dt, th, h2, h3, a.link-preise"
        ),
        "keys": ["operating_hours", "season", "prices"],
        "strict": False,  # because it often has trailing colons
    },
    "main_special": {
        "page": "main",
        "selector": "div, span, a",
        "keys": ["day_ticket"],
        "strict": False,
    },
    "loipen": {
        "page": "loipen",
        "selector": "dt, .loipen-bericht dt, th",
        "keys": ["trail_report", "classical", "skating"],
        "strict": False,
    },
    "values": {
        "page": "snow",
        "selector": "dd, span, div",
        "keys": ["today", "yesterday", "from"],
        "strict": False,
    },
}

OPTIONAL_KEYS = ["today", "yesterday"]

# bergfex removes the entire snow-report block outside the winter season, so keys
# living on those pages are legitimately absent in summer. Keys on the main page
# (season dates, prices, operating hours) are published year-round - if those
# vanish, the site was restructured and the parser is about to break.
SEASONAL_PAGES = {"snow", "loipen"}

# Deliberately narrow. The reference resorts are a mix of glaciers (Stubai,
# Soelden, Hintertux) and ordinary areas (Ramsau, Axamer Lizum), and in October
# and November only the glaciers report, so insisting on a snow report then would
# produce false alarms - the one failure mode a canary must not have. December to
# March every reference area is running, and that is also when a broken parser
# actually hurts users. Restructures outside this window are still caught by the
# year-round keys, which bergfex publishes all summer.
IN_SEASON_MONTHS = {12, 1, 2, 3}


def key_is_seasonal(key):
    """Whether a key may legitimately disappear outside the winter season."""
    for cfg in GROUPS.values():
        if key in cfg["keys"]:
            return cfg["page"] in SEASONAL_PAGES
    return False


def in_season(today=None):
    """Whether the snow report is expected to exist right now.

    BERGFEX_FORCE_SEASON overrides the calendar so either branch can be exercised
    on demand: `BERGFEX_FORCE_SEASON=1` treats today as mid-winter.
    """
    override = os.environ.get("BERGFEX_FORCE_SEASON")
    if override is not None:
        return override.strip().lower() in ("1", "true", "yes")
    return (today or datetime.date.today()).month in IN_SEASON_MONTHS

TARGET_RESORTS = [
    {
        "name": "Stubai",
        "path": "/stubaier-gletscher/",
    },
    {
        "name": "Cortina",
        "path": "/cortina-dampezzo/",
        "loipen_path": "/veneto/langlaufen/cortina-dampezzo/loipen/",
    },
    {
        "name": "Soelden",
        "path": "/soelden/",
        "loipen_path": "/tirol/langlaufen/soelden/loipen/",
    },
    {"name": "Les Saisies", "path": "/les-saisies/"},
    {"name": "Hintertux", "path": "/hintertux/"},
    {
        "name": "Ramsau",
        "path": "/ramsau-am-dachstein/",
        "loipen_path": "/steiermark/langlaufen/ramsau/loipen/",
    },
    {"name": "Axamer Lizum", "path": "/axamer-lizum/"},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def sanitize(text):
    if not text:
        return ""
    text = text.strip().rstrip(":")
    return " ".join(text.split()).lower()


def get_group_elements(soup, selector):
    if not soup:
        return []
    results = []
    for el in soup.select(selector):
        text = sanitize(el.get_text())
        if text and len(text) < 150:
            results.append(text)
    return results


async def fetch_html_async(session, url, retries=50):
    for i in range(retries):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                if response.status in [429, 404]:
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                    continue
        except Exception:
            continue
    return None


async def build_baseline(session):
    print("Building Stricter Global Baseline Mapping (AT)...")
    global_baseline = {}
    at_keywords = KEYWORDS["at"]

    # Scanners include major resorts and the overview page
    scanners = []
    for resort in TARGET_RESORTS:
        scanners.append(("resort", resort))

    # Add overview page as a virtual resort for header detection
    scanners.append(
        (
            "overview",
            {
                "name": "Overview AT",
                "path": "/oesterreich/schneewerte/",
            },
        )
    )

    for stype, resort in scanners:
        print(f"  Scanning {resort['name']}...")
        pages = {}
        if stype == "overview":
            pages["snow"] = f"https://www.bergfex.at{resort['path']}"
        else:
            pages["snow"] = f"https://www.bergfex.at{resort['path']}schneebericht/"
            pages["main"] = f"https://www.bergfex.at{resort['path']}"
            if "loipen_path" in resort:
                pages["loipen"] = f"https://www.bergfex.at{resort['loipen_path']}"

        for ptype, url in pages.items():
            html = await fetch_html_async(session, url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")

            for group_name, cfg in GROUPS.items():
                if cfg["page"] != ptype:
                    continue
                elements = get_group_elements(soup, cfg["selector"])

                for key in cfg["keys"]:
                    if key in global_baseline:
                        continue
                    target_kw = sanitize(at_keywords[key])

                    best_match = None
                    best_len = 999

                    for i, text in enumerate(elements):
                        # Use exact match if group is marked as strict
                        match = (
                            (text == target_kw)
                            if cfg["strict"]
                            else (target_kw in text)
                        )

                        if match and len(text) < best_len:
                            best_match = (i, text)
                            best_len = len(text)

                    if best_match:
                        idx, text = best_match
                        global_baseline[key] = {
                            "resort": resort,
                            "group": group_name,
                            "index": idx,
                            "at_text": text,
                            "ptype": ptype,
                        }
                        print(
                            f"    - Found '{key}' in {resort['name']} ({group_name} index {idx}: '{text}')"
                        )

    missing = (
        {k for g in GROUPS.values() for k in g["keys"]}
        - set(global_baseline.keys())
        - set(OPTIONAL_KEYS)
    )
    if missing:
        # A key that never made it into the baseline is silently skipped for all
        # 18 languages, so this has to reach the exit code rather than scroll past.
        print(f"\nBaseline mapping incomplete! Missing keys: {sorted(missing)}")
    return global_baseline, missing


async def validate_language(session, lang_code, lang_info, global_baseline, semaphore):
    async with semaphore:
        domain = lang_info["domain"]
        lang_keywords = KEYWORDS[lang_code]
        lang_errors = []
        lang_shifts = []
        resort_caches = {}

        for key, info in global_baseline.items():
            resort = info["resort"]
            ptype = info["ptype"]
            group_cfg = GROUPS[info["group"]]

            if resort["name"] not in resort_caches:
                resort_caches[resort["name"]] = {}
            if ptype not in resort_caches[resort["name"]]:
                path = (
                    resort["loipen_path"]
                    if ptype == "loipen"
                    else (
                        resort["path"] + ("schneebericht/" if ptype == "snow" else "")
                    )
                )
                html = await fetch_html_async(session, f"{domain}{path}")
                resort_caches[resort["name"]][ptype] = (
                    BeautifulSoup(html, "html.parser") if html else None
                )

            soup = resort_caches[resort["name"]][ptype]
            actual_elements = get_group_elements(soup, group_cfg["selector"])
            expected_raw = lang_keywords.get(key, "MISSING_IN_CONST")
            expected = sanitize(expected_raw)

            if not actual_elements:
                # The selector matched nothing at all. Off-season this is normal;
                # in season it means the structure we parse is gone.
                lang_errors.append(
                    {
                        "kind": "absent",
                        "key": key,
                        "detail": f"{ptype} page of {resort['name']}: selector matched nothing",
                    }
                )
                continue

            idx = info["index"]
            if idx < len(actual_elements) and expected in actual_elements[idx]:
                continue

            # Check for shift
            found_at = -1
            for i, text in enumerate(actual_elements):
                if expected in text:
                    found_at = i
                    break

            if found_at != -1:
                lang_shifts.append(f"'{key}' shifted {idx} -> {found_at}")
            elif key not in OPTIONAL_KEYS:
                actual_text = (
                    actual_elements[idx]
                    if idx < len(actual_elements)
                    else "OUT_OF_BOUNDS"
                )
                lang_errors.append(
                    {
                        "kind": "mismatch",
                        "key": key,
                        "at": info["at_text"],
                        "expected": expected_raw,
                        "found": actual_text.capitalize(),
                    }
                )

        if lang_errors:
            mismatches = sum(1 for e in lang_errors if e["kind"] == "mismatch")
            absent = len(lang_errors) - mismatches
            print(
                f"[{lang_code.upper()}] {mismatches} mismatches, {absent} absent structures."
            )
            return lang_code, lang_errors, lang_shifts
        else:
            print(f"[{lang_code.upper()}] OK.")
            return lang_code, [], lang_shifts


async def main():
    async with aiohttp.ClientSession() as session:
        global_baseline, baseline_gaps = await build_baseline(session)
        if not global_baseline:
            print("\nCRITICAL: No baseline could be built at all. Aborting.")
            sys.exit(1)

        print("\nStarting Async Cross-Language Validation...")
        semaphore = asyncio.Semaphore(3)
        tasks = []
        for lang_code, lang_info in SUPPORTED_LANGUAGES.items():
            if lang_code == "at":
                continue
            tasks.append(
                validate_language(
                    session, lang_code, lang_info, global_baseline, semaphore
                )
            )

        results = await asyncio.gather(*tasks)
        report(results, baseline_gaps)


def report(results, baseline_gaps):
    """Turn the three outcomes into a verdict.

    A mismatch always fails. An absent structure fails too, unless it is a
    snow-report key outside the winter season - bergfex removes that block every
    summer, which is the one case we must not cry wolf about.
    """
    mismatches = [e for _, errs, _ in results for e in errs if e["kind"] == "mismatch"]
    absences = [e for _, errs, _ in results for e in errs if e["kind"] == "absent"]
    clean = sum(1 for _, errs, _ in results if not errs)

    absent_keys = {e["key"] for e in absences} | set(baseline_gaps)
    seasonal_absent = {k for k in absent_keys if key_is_seasonal(k)}
    year_round_absent = absent_keys - seasonal_absent
    winter = in_season()

    print("\n" + "=" * 60)
    print(
        f"SUMMARY: {clean} languages clean, {len(mismatches)} mismatches, "
        f"{len(absences)} absent structures"
    )
    print(f"Season: {'in season' if winter else 'off-season'}")
    print("=" * 60)

    if mismatches:
        print("\nKeyword mismatches (shifts ignored):")
        print(f"{'LANG':<6} | {'KEY':<18} | {'AT BASELINE':<25} | {'EXPECTED':<25} | FOUND")
        print("-" * 100)
        for lang, errs, _ in results:
            for e in errs:
                if e["kind"] == "mismatch":
                    print(
                        f"{lang.upper():<6} | {e['key']:<18} | {e['at']:<25} | "
                        f"{e['expected']:<25} | {e['found']}"
                    )

    if baseline_gaps:
        print(
            f"\nNever reached validation - absent from the AT baseline: "
            f"{sorted(baseline_gaps)}"
        )

    if year_round_absent:
        print(
            f"\nCRITICAL: year-round structure is missing: {sorted(year_round_absent)}"
        )
        print("These are published outside the winter season too, so this is not")
        print("seasonality - the page was restructured and the parser will break.")

    if seasonal_absent:
        label = "CRITICAL" if winter else "EXPECTED"
        print(f"\n{label}: snow-report structure is missing: {sorted(seasonal_absent)}")
        if not winter:
            print("bergfex drops this block off-season. It cannot be verified until")
            print("the resorts reopen - re-run this check once they do.")

    failed = bool(mismatches) or bool(year_round_absent) or (winter and seasonal_absent)

    if failed:
        sys.exit(1)

    if seasonal_absent:
        print("\nNo mismatches found, but the snow report could not be verified.")
    else:
        print("\nValidation successful - every tracked structure was found.")


if __name__ == "__main__":
    asyncio.run(main())
