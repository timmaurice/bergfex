# Changelog

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] — unreleased

The `2.4.0` line was never released. Its three betas (`2.4.0b1`, `2.4.0b2`,
`2.4.0b3`) shipped only as pre-releases; everything they contained is part of
`3.0.0` and is listed below. Upgrading straight from `2.3.1` loses nothing.

### Breaking

- **The Lovelace card is now part of this integration.** It is served from
  `/bergfex_frontend/bergfex-card.js` and registered as a Lovelace resource
  automatically. Users of the standalone
  [lovelace-bergfex-card](https://github.com/timmaurice/lovelace-bergfex-card)
  should uninstall it from HACS. The integration removes the stale resource entry
  on startup and raises a repair issue reminding you to remove the repository
  itself; until you do, HACS keeps offering updates for a card you no longer use.
- Automatic resource registration requires Lovelace in storage mode. In YAML mode
  the integration logs a warning and you add the resource yourself.
- **The `season_start` and `season_end` attributes are gone.** They followed
  whichever operating period bergfex was displaying, which outside winter is the
  summer hiking season — so ski resorts reported as **Open** in August. They are
  replaced by explicit `winter_season_start` / `winter_season_end` and
  `summer_season_start` / `summer_season_end`. Automations and templates reading
  the old attributes need updating; in almost every case `winter_season_*` is what
  was meant.
- **`status` now means skiable, not in-season.** A resort is Open when its lifts
  are running, there is snow on the ground and it is inside opening hours. The
  season dates no longer decide it. Both alternatives were wrong at one end: lifts
  alone reported every valley resort as Open in August, when a single lift runs for
  hikers on bare grass, and the winter period alone reported the Hintertux glacier
  as Closed with 3 m of snow and three lifts turning.

### Added

- **Bundled Lovelace card** with visual editor, in five languages (da, de, en,
  fr, pl): table layout for comparing resorts, automatic alpine/cross-country
  detection, optional 24 h trend indicators, sorting, and the option to hide
  closed resorts.
- **Smart operational status** (#21): the Status sensor weighs both seasonal
  dates and daily operating hours instead of lift counts alone.
- **New status attributes**: `price`, `operating_hours_start`,
  `operating_hours_end`, and the winter and summer operating periods —
  `winter_season_start` / `_end`, `winter_operating_hours_start` / `_end` and the
  `summer_*` equivalents. These are read from bergfex's operating-hours panel
  structurally rather than by keyword, so they also work on domains where the
  localized labels differ.
- **The language can be changed after setup.** It now sits in the integration's
  options alongside the update interval, instead of being fixed at the moment the
  resort was added. Switching it moves the Bergfex domain with it and reloads the
  entry, so sensor values come back in the new language. The options dialog is also
  translated into all seven languages now, rather than only German and English.
- **Live-site validation scripts** (`check_live_site.py`, `e2e_report.py`) that
  detect structural changes on Bergfex before they break parsing.

### Fixed

- Out-of-season resorts were reported as **Open**. Status now respects the
  extracted season and operating-hour boundaries.
- Seasonal dates are fetched from the resort's main page when a subpage such as
  `/schneebericht/` omits them.
- Cross-country (Loipen) reports returned 404 because of wrong URL generation.
- Resort names went missing after a Bergfex layout change.
- Parsing handles Bergfex's newer span-based layouts alongside the older ones.
- Keyword fixes across 17 languages, including Italian `Stagione` / `Orario`
  and corrected `operating_hours` and `slope_condition` translations.
- A `null` entry in the card's `resorts` config no longer throws while resolving
  device IDs.

### Security

- `lxml` raised to `>=6.1.1`, covering an XXE vulnerability (CVE-2026-41066).

### Infrastructure

- Rollup, TypeScript, ESLint, Prettier and Vitest toolchain for the card, with a
  Frontend workflow running lint, format check, tests and build on every push.
- The release workflow builds the card before packaging, so `bergfex.zip` can
  never contain a stale bundle.
- Dependabot tracks npm dependencies weekly alongside pip and GitHub Actions.
- Dependency management moved to root-level `requirements.txt` and
  `requirements-test.txt`.

## [2.3.1] — 2026-03-15

Options flow stability fix.

## [2.3.0] — 2026-03-15

Precision slopes, custom polling, and cross-country revival.
