# Bergfex Integration Scripts

This directory contains utility scripts for maintaining and validating the Bergfex Home Assistant integration.

## Core Scripts

### 1. `check_live_site.py`
**Purpose**: Validates the structural integrity of the Bergfex website and ensures that all localized keywords in `const.py` still match the live site.
- **Usage**: `./venv/bin/python3 scripts/check_live_site.py`
- **When to use**: Run this after Bergfex updates their website or when adding support for a new language. It uses a "Golden Baseline" (AT) to detect positional shifts and ensures all languages stay in sync.

### 2. `e2e_report.py`
**Purpose**: Performs a full end-to-end (E2E) validation across all 18 supported languages.
- **Usage**: `./venv/bin/python3 scripts/e2e_report.py`
- **When to use**: Run this to verify the entire integration stack (fetching, parsing, and attribute mapping) against live data. It uses an aggressive "rapid-retry" strategy to bypass Bergfex's rate-limiting.

### 3. `maintain_const.py`
**Purpose**: A utility script for maintaining the `const.py` file.
- **Usage**: `./venv/bin/python3 scripts/maintain_const.py`
- **When to use**: Use this for automated updates or checks on the constants file.

## Execution
All scripts should be executed from the project root using the virtual environment:
```bash
./venv/bin/python3 scripts/<script_name>.py
```
