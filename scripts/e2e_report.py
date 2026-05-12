import asyncio
import aiohttp
import sys
import os
import random

# Ensure we can import the component
sys.path.insert(0, os.getcwd())
from custom_components.bergfex.const import SUPPORTED_LANGUAGES
from custom_components.bergfex.parser import parse_resort_page

# Most stable and widely available paths on all domains
ALPINE_PATH = "/stubaier-gletscher/schneebericht/"
CC_PATH = "/suedtirol/langlaufen/drei-zinnen-dolomiten/loipen/"


async def fetch_burst(session, url, lang_code, resort_name):
    # "reload 100 times fast till the 429 error is gone"
    # We use a burst retry with minimal delay (0.5s) to attempt to slip through the WAF.
    for attempt in range(100):
        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120,124)}.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                if response.status == 429:
                    if (attempt + 1) % 25 == 0:
                        print(
                            f"    [{lang_code.upper()}] {resort_name}: 429 Blocked (Attempt {attempt+1}/100)..."
                        )
                    await asyncio.sleep(0.4)  # Fast retry
                    continue
                return f"ERROR_{response.status}"
        except Exception as e:
            await asyncio.sleep(0.4)
    return "FAILED"


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
                html = await fetch_burst(session, url, lang_code, resort_name)

                if (
                    html
                    and not html.startswith("ERROR")
                    and not html.startswith("FAILED")
                ):
                    try:
                        data = parse_resort_page(html, lang=lang_code)
                        results.append(
                            {
                                "lang": lang_code.upper(),
                                "resort": resort_name,
                                "type": "CC" if is_cc else "ALP",
                                "data": data,
                            }
                        )
                        print(f"    ✅ {resort_name} Success")
                    except Exception as e:
                        print(f"    ❌ {resort_name} Parse Error")
                else:
                    print(f"    ❌ {resort_name} Failed: {html}")

                # Small jittered pause between types
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # Small jittered pause between languages
            await asyncio.sleep(random.uniform(1, 2))

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
