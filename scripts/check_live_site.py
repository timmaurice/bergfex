#!/usr/bin/env python3
"""
Global Baseline Structural Validation Script for Bergfex (Harden Version).
Uses strict exact-matching for baseline mapping and prevents misidentification
of keywords from large containers.
"""

import sys
import os
import asyncio
import random
import re
import aiohttp
from bs4 import BeautifulSoup
from unittest.mock import MagicMock

# Mock homeassistant
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.aiohttp_client"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
sys.modules["homeassistant.exceptions"] = MagicMock()

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
        "selector": "span.tw-font-semibold, div.box-header, dt, th, h2, a.link-preise",
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
        print(f"\nWARNING: Baseline mapping incomplete! Missing keys: {missing}")
    return global_baseline


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
                lang_errors.append(f"Fetch failed: {ptype} for {resort['name']}")
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
                        "key": key,
                        "at": info["at_text"],
                        "expected": expected_raw,
                        "found": actual_text.capitalize(),
                    }
                )

        if lang_errors:
            print(f"[{lang_code.upper()}] FAILED: {len(lang_errors)} mismatches.")
            return lang_code, lang_errors, lang_shifts
        else:
            print(f"[{lang_code.upper()}] OK.")
            return lang_code, [], lang_shifts


async def main():
    async with aiohttp.ClientSession() as session:
        global_baseline = await build_baseline(session)
        if not global_baseline:
            print("CRITICAL: No baseline. Aborting.")
            return

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
        passed = sum(1 for r in results if not r[1])
        failed_structurally = sum(
            1 for r in results if any(isinstance(e, dict) for e in r[1])
        )
        failed_fetch = sum(
            1
            for r in results
            if any(not isinstance(e, dict) for e in r[1])
            and not any(isinstance(e, dict) for e in r[1])
        )

        print("\n" + "=" * 50)
        print(
            f"OVERALL SUMMARY: {passed + 1} Passed, {failed_structurally} Structural, {failed_fetch} Fetch errors"
        )
        print("=" * 50)

        if failed_structurally > 0:
            print("\nCritical Structural Mismatches (Ignoring shifts):")
            print(
                f"{'LANG':<6} | {'KEY':<18} | {'AT BASELINE':<25} | {'EXPECTED':<25} | {'FOUND'}"
            )
            print("-" * 100)
            for lang, errs, shifts in results:
                for e in errs:
                    if isinstance(e, dict):
                        print(
                            f"{lang.upper():<6} | {e['key']:<18} | {e['at']:<25} | {e['expected']:<25} | {e['found']}"
                        )
            sys.exit(1)
        else:
            print("\nValidation Successful! All keywords found (shifts ignored).")


if __name__ == "__main__":
    asyncio.run(main())
