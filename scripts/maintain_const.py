#!/usr/bin/env python3
import sys
import os
import importlib.util

# Add custom_components to path to import bergfex.const
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
const_path = os.path.join(base_dir, "custom_components", "bergfex", "const.py")

spec = importlib.util.spec_from_file_location("bergfex_const", const_path)
const = importlib.util.module_from_spec(spec)
spec.loader.exec_module(const)

REQUIRED_KEYS = [
    "mountain",
    "valley",
    "snow_depth",
    "snow_condition",
    "last_snowfall",
    "avalanche",
    "lifts",
    "pistes",
    "slope_condition",
    "prices",
    "day_ticket",
    "today",
    "yesterday",
    "from",
    "operation",
    "classical",
    "skating",
    "trail_report",
    "countries",
    "values",
    "operating_hours",
    "season",
]

COUNTRY_ORDER = list(const.COUNTRIES.keys())


def validate():
    errors = []

    # Check that all supported languages have keywords
    for lang_code in const.SUPPORTED_LANGUAGES:
        if lang_code not in const.KEYWORDS:
            errors.append(f"Missing keywords for language: {lang_code}")
            continue

        keywords = const.KEYWORDS[lang_code]

        # Check for missing keys
        for key in REQUIRED_KEYS:
            if key not in keywords:
                errors.append(f"Language {lang_code} is missing key: {key}")

        # Check country list and sorting
        if "countries" in keywords:
            lang_countries = list(keywords["countries"].keys())
            if lang_countries != COUNTRY_ORDER:
                errors.append(
                    f"Language {lang_code} has incorrect country order or missing countries."
                )
                errors.append(f"  Expected: {COUNTRY_ORDER}")
                errors.append(f"  Got:      {lang_countries}")

        # Detect suspicious keywords (German/English leaks in other languages)
        suspicious_terms = ["Betrieb", "Saison", "Operation"]
        if lang_code not in ["at", "en", "fr", "hr"]:
            for key in ["operation", "operating_hours", "season"]:
                if key in keywords and keywords[key] in suspicious_terms:
                    errors.append(
                        f"Language {lang_code} has suspicious '{key}': '{keywords[key]}'"
                    )

    if errors:
        print("Validation failed with the following errors:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    else:
        print("Validation successful! All keywords and country lists are consistent.")
        sys.exit(0)


if __name__ == "__main__":
    validate()
