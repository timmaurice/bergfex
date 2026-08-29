# Bergfex Integration Scripts

This directory contains utility scripts for maintaining and validating the Bergfex Home Assistant integration.

## Core Scripts

### 1. `check_live_site.py`

**Purpose**: Validates the structural integrity of the Bergfex website and ensures that all localized keywords in `const.py` still match the live site.

- **Usage**: `./venv/bin/python3 scripts/check_live_site.py`
- **When to use**: Run this after Bergfex updates their website or when adding support for a new language. It uses a "Golden Baseline" (AT) to detect positional shifts and ensures all languages stay in sync. Runs daily via the `Live Website Check` workflow.
- **Exit code**: fails on a keyword mismatch, on missing year-round structure (season dates, prices, operating hours), and on a missing snow report during the winter season. Outside the season the snow report is reported as unverifiable without failing, because bergfex removes that block every summer. Set `BERGFEX_FORCE_SEASON=1` to override the calendar.

### 2. `e2e_report.py`

**Purpose**: Performs a full end-to-end (E2E) validation across all 18 supported languages.

- **Usage**: `./venv/bin/python3 scripts/e2e_report.py`
- **When to use**: Run this to verify the entire integration stack (fetching, parsing, and attribute mapping) against live data. It uses an aggressive "rapid-retry" strategy to bypass Bergfex's rate-limiting.

### 3. `maintain_const.py`

**Purpose**: A utility script for maintaining the `const.py` file.

- **Usage**: `./venv/bin/python3 scripts/maintain_const.py`
- **When to use**: Use this for automated updates or checks on the constants file.

### 4. `build-release-zip.mjs`

**Purpose**: Builds and verifies `bergfex.zip`, the archive HACS extracts straight into a user's `custom_components/bergfex/`.

- **Usage**: `npm run build:release`, or `node scripts/build-release-zip.mjs --dry-run` to see what a release would ship without writing anything.
- **When to use**: Run it before tagging. CI runs it on every pull request and again during the release.
- It refuses to build when the `manifest.json` version disagrees with the release tag, when `manifest.json`, `__init__.py` or `bergfex-card.js` is missing, or when test fixtures, `__pycache__`, `.pytest_cache` or `.DS_Store` would reach users. Build the card first — the archive includes `bergfex-card.js`, not the TypeScript sources.

## Execution

All scripts should be executed from the project root using the virtual environment:

```bash
./venv/bin/python3 scripts/<script_name>.py
```
