# Changelog

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] — 2026-09-26

### Added

- **Reconfigure a ski area to switch its language** (#46). The entry's
  Reconfigure step offers the eighteen languages of the setup flow, prefilled
  with the current one. The language selects the Bergfex domain, so the area's
  page is loaded from the new domain first; if that fails the form says so and
  the entry is left as it was. Entity IDs, history and the device stay, because
  a resort's path is the same on every domain.
- **Config entry diagnostics** (#43): the entry's settings, the state of the
  last poll, a summary per area of what the page yielded, and whether the
  forecast and season caches are serving it. The webhook URL is redacted
  wherever it appears.
- **The card works with a keyboard and a screen reader** (#41). Every figure is
  a button whose accessible name reads label, value and trend; Conditions and
  Snow Forecast are toggle buttons with `aria-expanded`; the forecast tabs are a
  real tab list with arrow, Home and End keys; the carousel arrows, the map and
  the Bergfex link are named. The new strings are in all eight card languages,
  and nothing looks different.
- **A live preview in the card picker.** The "Add card" dialog showed the card
  as a bare name tile.

### Changed

- **The options only set the update interval.** The language moved to
  Reconfigure (#46); in 3.0.0 it sat next to the interval under Configure.
- **The Last Update sensors are diagnostic entities** (#45). They are listed
  under Diagnostic on the device page and left off auto-generated dashboards.
  The entity ID is unchanged and the card still shows the time.
- **Sensor icons come from `icons.json`.** The sensors no longer carry an
  `icon` state attribute. The Status sensor of a cross-country area keeps
  `icon: mdi:ski-cross-country`, which the card reads to tell it from an alpine
  one.
- **Home Assistant 2026.9.1 or newer is required**, up from 2026.9.0, matching
  the oldest core the tests run against.

### Fixed

- **A resort added twice stopped updating in its second entry** once the first
  was reloaded, for example after changing its options. The second entry used
  the first one's coordinator; each entry now polls on its own.
- The Bergfex link's tooltip showed the raw key
  `component.bergfex-card.card.link_title`.

### Infrastructure

- Each entry keeps its coordinator in `runtime_data` (#40), the coordinator
  lives in `coordinator.py` (#42), and the sensor and image platforms declare
  `PARALLEL_UPDATES`.
- A test holds `hacs.json` to the `MINIMUM_CORE` of the test workflow.
- `FUNDING.yml` added (#44). `jsdom` bumped to 30.1.0 (#38).

## [3.0.1] — 2026-09-24

### Added

- **Danish translation of the integration.** The setup flow, the options, every
  entity name and the repair messages are now translated into Danish. The card
  already had a Danish translation; the integration around it spoke English.
- **The card's Danish now uses the same words as the integration** — løjper for
  cross-country trails, sneudsigt for the snow forecast, entiteter for entities —
  and fixes a few split compounds.

### Fixed

- **The editor's resort field is called Resorts in English.** It read "Resort
  Entities" although it picks devices, not entities, and the error for an empty
  list asked for a resort entity.

### Changed

- Dependencies updated to their latest minor versions.

## [3.0.0] — 2026-09-12

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
  are running, there is snow on the ground, it is inside opening hours, and its
  terrain is actually prepared. Where Bergfex publishes open-piste figures those
  decide; where the piste row is missing entirely, the winter season stands in.
  Lifts alone reported every valley resort as Open in August — Serfaus runs all
  eleven for hikers — and snow depth alone reported the Hintertux glacier as Open
  on three metres of old snow while its operator showed 0 km of prepared piste.

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
- **A repair that clears out entities older versions left behind.** The
  integration has keyed its entities three ways over its life, and where an
  install carries rows from more than one scheme the superseded ones sit on the
  device with nothing behind them - which is what the duplicate forecast images
  were. The repair lists and counts them; nothing is deleted until the user
  confirms it, and leaving them alone is a valid answer.
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
- **New `operation_status` attribute** on the resort status sensor, carrying
  bergfex's own operating word ("täglich", "ogni giorno", "Geschlossen") rather
  than the opening times it used to be mixed up with.
- Opening times were not read on most pages. bergfex labels them differently
  almost everywhere - `Betriebszeiten`, `Opening times`, `Ouverture`, `Godziny` -
  and on the German and Italian pages the keyword in `const.py` names the status
  field instead, so a resort carrying both fields yielded no
  `operating_hours_start` / `_end` at all. They are now read from the value that
  is a time range and nothing else, which holds in every language.
- A resort that closes over lunch lost its afternoon: only the first of the two
  published ranges was read.
- `operation_status` could be a fragment of the times rather than a status -
  "von" out of "von 09:00 - 16:45 Uhr", or a whole malformed "9:5 - 16:00". It
  stays unset when what is left is not a plausible status.
- The card missed a locale change. `shouldUpdate` compared only `hass.language`,
  while the forecast date and the season teaser format against `hass.locale` and
  every number goes through `locale.number_format`, so a locale-only profile
  change left the old format on screen until something else re-rendered the card.
- Forecast dates name the month (`Fri, 12 Apr`) instead of numbering it
  (`Fri, 12/04`), matching the season teaser rather than contradicting it.
- A config entry that failed to set up said nothing at all: Home Assistant
  reports `ConfigEntryNotReady` at INFO, which the default log level hides, and
  the reason was not carried in the exception either, so the entry page showed
  an empty one. The first failed attempt now logs a warning naming the resort
  and the reason, retries stay at DEBUG, and the reason reaches the UI.

- **Duplicate forecast images.** Sölden offered twelve daily images and ten
  summaries instead of six and five, every second one rendering "Image not
  available" and shifting the dates after it. The card now ignores registry rows
  Home Assistant marks as restored.
- **`operation_status` was missing in fourteen of the eighteen languages.**
  bergfex labels the field differently depending on the page, and only four
  languages had recorded the spelling the snow report uses. French recorded
  neither - its pages say "Heures d'ouverture", not "Ouverture".
- **"No report" leaked into the card in fourteen languages.** The phrase each
  language was checked against is not the one bergfex serves - `nincs jelentés`
  against `nincs üzenet`, `žádná zpráva` against `žádné hlášení` - so the
  wording was printed verbatim instead of being greyed out as unknown. Re-read
  off live pages in all eighteen.
- **Devices named after the URL instead of the resort** - `achensee` rather than
  `Achensee` - on any entry added while the Tailwind breakage above was live. A
  device the user renamed keeps their name.
- **The "uninstall the standalone card" repair never went away**, even once the
  card was gone. It was raised on the single run that removed the stale Lovelace
  resource and never re-checked, so complying with it looked the same as
  ignoring it. It now tracks whether the HACS files are still on disk.
- **Region and country snow reports were requested at `/schneewerte/`**, which
  bergfex now serves only as a redirect and 404s for paths it no longer
  recognises.
- **A resort could be parsed as its own region**, producing URLs that 404 on
  every poll - the snow report and all six forecast pages.
- A deprecated `device_registry.async_get_device` call that Home Assistant drops
  in 2027.8.0.
- **The card was sized wrongly in the sections grid.** It handed the grid its
  masonry size - a hand-maintained model of its own layout, in the wrong unit -
  which could not account for what the card actually renders: a resort whose
  sensor is missing, or an accordion the user has collapsed. Home Assistant now
  measures the rendered card itself.
- **The 24-hour trend arrows never appeared on a freshly loaded dashboard**, and
  then queried the recorder far too often. Home Assistant creates a card, calls
  `setConfig`, and only afterwards hands it `hass` - so the history fetch, which
  ran from `setConfig`, always ran with no connection to fetch over. On later
  updates the opposite happened: the guard compared against a config that had not
  changed, so it was always true, and since Home Assistant hands every card a new
  `hass` whenever any entity in the instance changes, a busy instance produced
  several history queries a second. The baseline is now read once per change that
  could affect it, and re-read hourly because the 24-hour window slides even when
  nothing on the page moves.

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
