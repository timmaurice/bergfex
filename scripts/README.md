# Bergfex Integration Scripts

This directory contains utility scripts for maintaining and validating the Bergfex Home Assistant integration.

## Core Scripts

### 1. `check_live_site.py`

**Purpose**: Validates the structural integrity of the Bergfex website and ensures that all localized keywords in `const.py` still match the live site.

- **Usage**: `./venv/bin/python3 scripts/check_live_site.py`
- **When to use**: Run this after Bergfex updates their website or when adding support for a new language. It uses a "Golden Baseline" (AT) to detect positional shifts and ensures all languages stay in sync. Runs daily via the `Live Website Check` workflow.
- **Politeness**: one request at a time, two seconds apart, identifying as Home Assistant. A 429 is retried at most twice, after the `Retry-After` it names or an exponential back-off, and the wait holds back every other request too. A 403 or 451 is never retried. The rules live in `_polite.py`, shared with `e2e_report.py`.
- **Exit code**: fails on a keyword mismatch, on missing year-round structure (season dates, prices, operating hours), and on a missing snow report during the winter season. Outside the season the snow report is reported as unverifiable without failing, because bergfex removes that block every summer. Set `BERGFEX_FORCE_SEASON=1` to override the calendar.
- **Unverified languages**: a language whose pages never loaded is reported as unverified and counted separately in the summary — never as clean, and never ending in "Validation successful". It does not fail the run, for the same reason refusals do not: a refused runner says nothing about a home connection.

### 2. `e2e_report.py`

**Purpose**: Performs a full end-to-end (E2E) validation across all 18 supported languages.

- **Usage**: `./venv/bin/python3 scripts/e2e_report.py`
- **When to use**: Run this to verify the entire integration stack (fetching, parsing, and attribute mapping) against live data. It fetches with the same polite rules as `check_live_site.py` (see `_polite.py`), so a full run takes a few minutes. A page bergfex refuses is reported with its status rather than retried until it gives in.

### 3. `maintain_const.py`

**Purpose**: A utility script for maintaining the `const.py` file.

- **Usage**: `./venv/bin/python3 scripts/maintain_const.py`
- **When to use**: Use this for automated updates or checks on the constants file.

### 4. `build-release-zip.mjs`

**Purpose**: Builds and verifies `bergfex.zip`, the archive HACS extracts straight into a user's `custom_components/bergfex/`.

- **Usage**: `npm run build:release`, or `node scripts/build-release-zip.mjs --dry-run` to see what a release would ship without writing anything.
- **When to use**: Run it before tagging. CI runs it on every pull request and again during the release.
- It refuses to build when the `manifest.json` version disagrees with the release tag, when `manifest.json`, `__init__.py` or `bergfex-card.js` is missing, or when test fixtures, `__pycache__`, `.pytest_cache` or `.DS_Store` would reach users. Build the card first — the archive includes `bergfex-card.js`, not the TypeScript sources.

### 5. `check_season_start.py`

**Purpose**: Watches for the point at which refreshing the HTML fixtures becomes worthwhile — when the reference resorts start reporting open pistes.

- **Usage**: `PYTHONPATH=. python3 scripts/check_season_start.py`
- **When to use**: Runs daily from September via the `Season Watch` workflow, which opens an issue once it fires. Run it by hand to see where the resorts stand.
- It reuses the integration's own `evaluate_status`, so the watcher cannot drift away from what the integration considers open. That means fetching the resort's main page as well, for the operating panel — without it a summer glacier parses season-less and reads as open.
- Two groups are watched separately because they open weeks apart: the glaciers on the first real snowfall, and the valley resorts in late November or December. Each raises its own issue with its own checklist.

## Execution

All scripts should be executed from the project root using the virtual environment:

```bash
./venv/bin/python3 scripts/<script_name>.py
```
