import asyncio
import aiohttp
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _integration import import_integration_module  # noqa: E402
from _polite import fetch_html  # noqa: E402

# The leaf modules only, so this runs without Home Assistant installed.
SUPPORTED_LANGUAGES = import_integration_module("const").SUPPORTED_LANGUAGES
parse_resort_page = import_integration_module("parser").parse_resort_page

# Most stable and widely available paths on all domains
ALPINE_PATH = "/stubaier-gletscher/schneebericht/"
CC_PATH = "/suedtirol/langlaufen/drei-zinnen-dolomiten/loipen/"


async def fetch_page(session, url, lang_code, resort_name):
    """Fetch politely - see _polite.py - and say why a page did not come back.

    This used to reload up to a hundred times with a spoofed Chrome User-Agent
    to slip past bergfex's rate limit. A refusal is now taken as one.
    """
    statuses = []

    def remember(response):
        statuses.append(response.status)
        retry_after = response.headers.get("retry-after") or "-"
        print(
            f"    [{lang_code.upper()}] {resort_name}: {response.status} "
            f"(retry-after {retry_after})"
        )

    html = await fetch_html(session, url, on_refusal=remember)
    if html is not None:
        return html
    return f"ERROR_{statuses[-1]}" if statuses else "FAILED"


async def run_report():
    async with aiohttp.ClientSession() as session:
        print(
            "\nStarting Comprehensive Multilingual E2E Report (Alpine + CC per Country)"
        )
        print("=" * 120)

        results = []
        langs = list(SUPPORTED_LANGUAGES.keys())

        for i, lang_code in enumerate(langs):
            print(
                f"[{i+1}/{len(langs)}] Processing {SUPPORTED_LANGUAGES[lang_code]['name']} ({lang_code.upper()})..."
            )

            for resort_name, path, is_cc in [
                ("Stubai", ALPINE_PATH, False),
                ("3 Zinnen", CC_PATH, True),
            ]:
                url = f"{SUPPORTED_LANGUAGES[lang_code]['domain']}{path}"
                html = await fetch_page(session, url, lang_code, resort_name)

                if (
                    html
                    and not html.startswith("ERROR")
                    and not html.startswith("FAILED")
                ):
                    try:
                        data = parse_resort_page(html, path, lang_code)
                        results.append(
                            {
                                "lang": lang_code.upper(),
                                "resort": resort_name,
                                "type": "CC" if is_cc else "ALP",
                                "data": data,
                            }
                        )
                        print(f"    ✅ {resort_name} Success")
                    except Exception:
                        print(f"    ❌ {resort_name} Parse Error")
                else:
                    print(f"    ❌ {resort_name} Failed: {html}")

        print("\n" + "=" * 145)
        print(
            f"| {'LANG':<5} | {'RESORT':<12} | {'TYPE':<5} | {'SNOW/TRAIL':<15} | {'LIFTS/KM':<12} | {'CONDITION':<15} | {'STATUS':<10} |"
        )
        print("-" * 145)

        # Sort by Lang then Type
        results.sort(key=lambda x: (x["lang"], x["type"]))

        for r in results:
            d = r["data"]
            if r["type"] == "ALP":
                snow = f"{d.get('snow_mountain', 'N/A')}/{d.get('snow_valley', 'N/A')}"
                metrics = f"{d.get('lifts_open_count', 'N/A')}/{d.get('lifts_total_count', 'N/A')}"
                cond = str(d.get("snow_condition", "N/A"))[:15]
            else:
                snow = str(d.get("trail_report", "N/A"))[:15]
                metrics = f"{d.get('classical_open_km', 'N/A')}/{d.get('skating_open_km', 'N/A')} km"
                cond = str(d.get("slope_condition", "N/A"))[:15]

            status = d.get("status", "N/A")
            print(
                f"| {r['lang']:<5} | {r['resort']:<12} | {r['type']:<5} | {snow:<15} | {metrics:<12} | {cond:<15} | {status:<10} |"
            )
        print("=" * 145)


if __name__ == "__main__":
    asyncio.run(run_report())
