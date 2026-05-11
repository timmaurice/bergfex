#!/usr/bin/env python3
"""
Global Baseline Structural Validation Script for Bergfex (Async Version).
Builds a master mapping from multiple 'Golden Resorts' and verifies all languages
concurrently. Treating positional shifts as SUCCESS but logging them for awareness.
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

# Configuration of structural groups to check
GROUPS = {
    "snow_report_big": {
        "page": "snow",
        "selector": "dt.big",
        "keys": ["mountain", "valley", "snow_depth"],
    },
    "snow_report_standard": {
        "page": "snow",
        "selector": "dt:not(.big)",
        "keys": [
            "snow_condition",
            "last_snowfall",
            "avalanche",
            "operation",
            "lifts",
            "pistes",
            "slope_condition",
        ],
    },
    "main_page_content": {
        "page": "main",
        "selector": "span.tw-font-semibold, div.box-header, dt, th, td, h2, a, div",
        "keys": ["operating_hours", "season", "prices", "day_ticket"],
    },
    "loipen_report": {
        "page": "loipen",
        "selector": "dt, .loipen-bericht dt, th",
        "keys": ["trail_report", "classical", "skating"],
    },
    "value_keywords": {
        "page": "snow",
        "selector": "dd, span, div",
        "keys": ["today", "yesterday", "from"],
    },
}

OPTIONAL_KEYS = ["today", "yesterday"]

TARGET_RESORTS = [
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
    """Clean text but keep brackets as they may contain keywords."""
    if not text:
        return ""
    text = text.strip().rstrip(":")
    text = " ".join(text.split())
    return text.lower()


def get_group_elements(soup, selector):
    """Get sanitized text for all elements matching selector, filtering out large containers."""
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
                return None
        except Exception:
            continue
    return None


async def build_baseline(session):
    print("Building Global Baseline Mapping (AT)...")
    global_baseline = {}
    at_keywords = KEYWORDS["at"]

    for resort in TARGET_RESORTS:
        print(f"  Scanning {resort['name']}...")
        pages = {
            "snow": f"https://www.bergfex.at{resort['path']}schneebericht/",
            "main": f"https://www.bergfex.at{resort['path']}",
        }
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
                        if target_kw in text and len(text) < best_len:
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
                            f"    - Found '{key}' in {resort['name']} ({ptype} index {idx}: '{text}')"
                        )

    missing = (
        {k for g in GROUPS.values() for k in g["keys"]}
        - set(global_baseline.keys())
        - set(OPTIONAL_KEYS)
    )
    if missing:
        print(f"\nWARNING: Baseline incomplete! Missing: {missing}")

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
            group_name = info["group"]
            group_cfg = GROUPS[group_name]

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
                lang_errors.append(f"Could not fetch {ptype} for {resort['name']}")
                continue

            idx = info["index"]
            if idx < len(actual_elements) and expected in actual_elements[idx]:
                continue  # Perfect positional match

            # Check for shift
            found_at = -1
            for i, text in enumerate(actual_elements):
                if expected in text:
                    found_at = i
                    break

            if found_at != -1:
                # Treating a shift as SUCCESS but logging it
                lang_shifts.append(f"'{key}' shifted from index {idx} to {found_at}")
            elif key not in OPTIONAL_KEYS:
                actual_text = (
                    actual_elements[idx]
                    if idx < len(actual_elements)
                    else "OUT_OF_BOUNDS"
                )
                lang_errors.append(
                    f"MISMATCH '{key}': expected '{expected_raw}', found '{actual_text.capitalize()}'"
                )

        if lang_errors:
            print(
                f"[{lang_code.upper()}] FAILED: {len(lang_errors)} mismatches ({len(lang_shifts)} shifts)."
            )
            return lang_code, lang_errors, lang_shifts
        else:
            status = f"OK ({len(lang_shifts)} shifts)" if lang_shifts else "OK"
            print(f"[{lang_code.upper()}] {status}.")
            return lang_code, [], lang_shifts


async def main():
    async with aiohttp.ClientSession() as session:
        global_baseline = await build_baseline(session)
        if not global_baseline:
            print("CRITICAL: No baseline. Aborting.")
            return

        print("\nStarting Async Cross-Language Validation...")
        semaphore = asyncio.Semaphore(3)  # Limit concurrency to stay under WAF
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
        failed = sum(1 for r in results if r[1])

        print("\n" + "=" * 50)
        print(f"OVERALL SUMMARY: {passed + 1} Passed (inc. AT), {failed} Failed")
        print("=" * 50)

        if failed > 0:
            print("\nCritical Mismatches (Ignoring shifts):")
            for lang, errs, shifts in results:
                for e in errs:
                    print(f"- [{lang.upper()}] {e}")
            sys.exit(1)
        else:
            print("\nValidation Successful! All keywords found (shifts ignored).")


if __name__ == "__main__":
    asyncio.run(main())
