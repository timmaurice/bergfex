# Bergfex 3.0.0 — Release & Card Retirement Plan

**Goal:** ship a polished `timmaurice/bergfex` 3.0.0 that bundles the Lovelace card,
then retire `timmaurice/lovelace-bergfex-card` from HACS and archive the repo.

## Context (as of 2026-08-29)

- **Glaciers report year round; valley resorts do not.** On 30 August Hintertux
  showed 305 cm and 14 `<dt>` elements, Schnalstal 50 cm, while Warth rendered
  **0** `<dt>` (the winter fixture has 20). An earlier note here claimed there was
  no live snow data anywhere — that was drawn from valley resorts only.
- **Nowhere is skiable yet.** No resort reports a single open piste; the Hintertux
  operator shows 3 lifts and 0 km prepared. That is what mid-September changes,
  and it is what the status rule turns on.
- **Everything else is live, though.** The test instance parses status, lift counts,
  elevations, prices and season dates right now (Serfaus: `Open`, 11/11 lifts,
  season 2026-06-13 → 2026-10-11). The card renders against that today, with the
  snow columns showing N/A — so layout, sorting, badges and the accordion are all
  verifiable before the season starts.
- Everything below marked _(offline)_ is verifiable today via the 27 HTML fixtures
  in `tests/fixtures/` (58 pytest + 33 vitest, all green).
- **Season anchors:**
  | Resort                 | Opening                                              |
  | ---------------------- | ---------------------------------------------------- |
  | Hintertuxer Gletscher  | partly year-round, regular season mid/late Sept 2026 |
  | Schnalstaler Gletscher | 18 Sept 2026                                         |
  | Pitztaler Gletscher    | 26 Sept 2026                                         |
- **Repos:** integration `timmaurice/bergfex` (19★, latest release 2.3.1),
  card `timmaurice/lovelace-bergfex-card` (10★, latest release 2.2.1; the local clone's
  remote `bergfex-card` is a rename redirect). HACS default lists the card at
  `plugin:690`, the integration at `integration:2949`. No open issues on either repo.

---

## Phase 0 — Now → 17 Sept (offline, fixture-driven)

### Migration blockers — do these first

- [x] **B1 — Remove stale card resources on setup.**
      `custom_components/bergfex/__init__.py:92` only reconciles resources whose URL
      starts with `/bergfex_frontend/`. A user upgrading from the HACS card keeps a
      second entry (`/hacsfiles/lovelace-bergfex-card/bergfex-card.js`, or a hand-rolled
      `/local/bergfex-card.js`) and loads the bundle **twice**.
      Extend the loop to delete any resource whose URL ends in `bergfex-card.js`
      and is not `new_url`.
- [x] **B2 — Guard the custom-element definition.**
      Both bundles use `@customElement(ELEMENT_NAME)` → `bergfex-card`
      (`frontend/src/bergfex-card.ts:63`, plus `bergfex-card-editor` in `editor.ts:39`).
      The second `customElements.define` throws at module scope, killing whichever
      copy loads second — card _and_ editor. Wrap in a `customElements.get(...)` check
      so a leftover HACS copy degrades instead of exploding.
- [x] **B3 — Decide the migration UX.** Options: silent cleanup (B1), a repair issue
      telling the user to uninstall the HACS card, or both. Recommend B1 + repair issue.
- [x] **B4 — Source parity check.** Diff `frontend/src/` against
      `../bergfex-card/src/` (card 2.2.1, last commit `fb516f7` "classical and skating
      trails detection") and confirm nothing was left behind in the move.

### Release hygiene _(offline)_

- [x] Stale releases on `timmaurice/bergfex` (draft `2.4.0b3`, pre-releases `2.4.0b2`
      / `2.4.0b1`): **keep them.** Their notes are folded into the 3.0.0 changelog;
      the releases themselves stay as history. Do not delete.
- [x] CHANGELOG for 2.3.1 → 3.0.0, with the 2.4.0 betas folded in and the skipped
      version line called out.
- [x] Verify `hacs.json` `zip_release` / `bergfex.zip` actually contains the built
      `bergfex-card.js`. It did — but the archive also shipped the 27 test fixtures,
      `__pycache__`, `.pytest_cache` and `.DS_Store` to every user: 56 of ~80 entries,
      759 K instead of 60 K. Excluded in `release.yml`, with a CI guard that fails the
      release if a required file is missing or junk creeps back in.
- [x] Move `tests/` out of `custom_components/bergfex/` to the repo root. The manual
      install now copies 416 K instead of 4 MB, and the component directory holds only
      what ships. Imports were already absolute, so nothing needed rewriting.
- [x] Verify `.github/workflows/release.yml` runs the rollup build **before** zipping,
      so the bundle can never ship stale.
- [x] README rewrite: one-install story, card config reference, explicit
      "migrating from lovelace-bergfex-card" section.

- [x] **Let the language be changed after setup.** The options flow now carries the
      language alongside the update interval. Changing it rewrites `CONF_DOMAIN` and
      the cached url, then reloads the entry; resort and country paths are identical
      on every bergfex domain and are left alone. The options dialog had only ever
      been translated for `de` and `en` — the other five now have it too.

### Quality _(offline)_

- [x] Fix the visual editor showing `[object Object]` / "Unknown device selected" for
      every resort written in the `{ device, name }` form, and silently dropping custom
      resort names on save.
- [x] Chase down what the canary found: bergfex has dropped the Tailwind `tw-` class
      prefix site-wide. `tw-text-4xl` and `tw-text-2xl` no longer appear at all, so
      the parser's resort-name branch never fired and names came out as
      `SchneeberichtSerfaus - Fiss - Ladis`. Both spellings are accepted now. Worth a
      wider sweep during the Phase 1 fixture refresh — other `tw-` selectors may be
      dead too, and the winter fixtures still carry the old markup, so the test suite
      cannot see it.
- [x] Card states already covered: cross-country has its own suite, and missing
      sensors are exercised through the `lifts_open` / `slopes_open` fallbacks, the
      "without total" cases and the absent-timestamp tests.
- [x] Step through all thirteen card options against the running instance. Twelve
      behave as specified; `sort_by: lift` did nothing and is fixed.
- [x] `hide_closed_resorts` now hides only genuinely closed resorts — those between
      the two seasons — instead of everything the status sensor calls Closed. A
      resort in summer operation is not closed; bergfex reports it as
      "Sommerbetrieb" and it may be running lifts. This removes the empty card the
      option produced from April to November without needing an empty state.
- [x] Add `show_trails` so cross-country details can be hidden. `show_snow` and
      `show_lifts_slopes` are scoped to ski resorts by design, so a cross-country
      resort used to keep its trail figures with every display option off. The new
      option sits in its own editor group, since the ski-only one does not apply.
- [x] Card: cover the two remaining degraded states. The partial-data case was
      already handled; the loading case turned up a real defect — the card kept
      rendering stale values when a resort's entities disappeared. - **loading** — `hass` is set but the coordinator has not delivered yet.
      Nothing asserts what the card renders in that window. - **partial data** — some sensors carry values while others are `unknown`,
      within the same resort row. Only covered field by field, never as a row.
- [x] Parse the winter season. bergfex publishes winter and summer operating periods
      side by side, keyed by an Alpine.js `x-show` expression that is identical in
      every language. Exposed as `winter_season_*` / `summer_season_*` attributes on
      the status sensor, fetched once per resort per restart and cached.
- [x] **Fix the status semantics.** `season_start` / `season_end` are removed; status
      is judged against the winter season alone, and winter operating hours are
      exposed alongside it. Verified in the test instance: Warth, Feldberg and
      Serfaus flipped from **Open** to **Closed**, and no `season_start` attribute
      remains. Resorts without an operating-hours panel (Les Saisies) now carry no
      season data at all, which is better than carrying the summer one.
- [x] **Off-season card appearance.** The badge is now four-valued instead of
      collapsing everything that is not running into a red "Closed":
      **Open** (green, unchanged operational state) · **Winter season** (green,
      muted — in season but not running right now) · **Summer season** (yellow) ·
      **Closed** (red, between the two periods). Resorts that publish no season at
      all fall back to the previous Open/Closed. Translated into all five languages.
- [x] Tease the winter start under the badge wherever the season is still ahead —
      under a summer badge and a plain closed one alike. A published future date
      reads "ab 04.12."; where bergfex still shows the finished season, the date is
      quoted as an estimate ("letztes Jahr: 05.12.") rather than passed off as this
      year's. Anything older than 18 months is dropped instead.

---

## Phase 1 — from mid-September: the season proper

The original premise here was wrong and is corrected below. Glaciers report **year
round** — on 30 August Hintertux showed 305 cm and Schnalstal 50 cm — so "the first
live data of the season" already exists. What actually arrives in September is
**prepared piste**, which is what the status rule now turns on, and which no resort
reports today. The Hintertux operator confirms it: 3 lifts, 0 km.

- [x] **Watch for the trigger.** `.github/workflows/season_watch.yml` runs daily
      from September and raises an issue once resorts start running prepared piste.
      Two groups, because they open weeks apart and mean different things: the
      glaciers first, on the first real snowfall, which no calendar predicts; the
      valley resorts in late November or December. Each carries its own checklist.
- [x] **Fixtures: captured, not refreshed — the blanket refresh was the wrong
      move and the attempt proves it.** All 26 capturable fixtures were re-fetched
      on 21 September and the suite went from 310 green to 26 red, every failure
      for want of data rather than for drift: Serfaus in September publishes no
      snow report at all, so the refresh replaced a populated report with an empty
      one and deleted the coverage that caught the eighteen-language keyword bugs.
      The losses were identical across all 18 languages and **nothing was gained
      anywhere** — no new field, no changed shape. That uniformity is the finding:
      there is no parser drift on the resort page.
      So the winter corpus stays, and three September captures are added beside
      it — `hintertux-glacier-open` (running: 25 cm, 4/21 lifts, two open pistes),
      `serfaus-off-season` (11/11 lifts for hikers, no snow behind them) and
      `overview-at-off-season` (the Austrian country page, 109 resorts, which had
      never had a captured page at all — only a six-row table written by hand).
      `cortina_loipen` was refreshed in place; it was already an empty summer page.
      The blanket refresh belongs to the **valley** trigger in `season_watch.yml`,
      in late November, when the live pages actually carry the winter shape. Today
      only the glacier trigger has fired. `scripts/refresh_fixtures.py` does the
      job when it is time — it reads each fixture's own canonical link rather than
      keeping a second list of urls, and leaves hand-written fixtures alone.
- [x] **`tw-` sweep: the prefix is gone from every page bergfex serves.** Zero
      occurrences across all 26 re-fetched pages, against ~2,100 per page before.
      Widened afterwards to six locales' main pages — the one page type the snow
      reports do not cover, and where the price selector lives: `tw-` zero on all
      six, `text-2xl` and `font-semibold` present on all six.
      **The dual-spelling support is now removed**, in both parser sites and the
      canary. What stood in the way was not the live site but the winter fixtures,
      which are pre-restyle captures and still carry `tw-text-4xl`: dropping the
      prefix turned 24 tests red, all of them on `resort_name` and nothing else.
      Hand-editing the class inside 26 captured pages would have made them
      something bergfex never served, so instead those tests now assert the name
      with `endswith` and say why — they exist for the language keyword map, and
      name parsing is covered against current markup in `test_current_markup.py`.
      `lelex-crozet.html` was hand-written rather than captured, so it was simply
      updated to the current spelling. Verified after removal: all 18 languages
      parse the resort name off freshly fetched pages, and price parsing is
      byte-identical across six locales.
      Every other class the parser hooks was audited at the same time, and three
      turned out to be dead: a table lookup whose two-class string could never
      match anything, the `breadcrumb-wrapper` fallback for the older page design
      (46 pages, all on `ul[aria-label="Breadcrumb"]`), and the
      `report-label`/`report-info`/`report-value` branch that read cross-country
      kilometres from a box layout. The last needed a witness rather than an
      absence — a cross-country area that is not grooming renders no report at
      all, so September silence proves nothing — and three areas are reporting
      right now (Ramsau on two domains, Obertauern), all through the `<dl>` the
      surviving branch reads. All three removed, verified behaviour-neutral over
      105 pages × 4 parser entry points.
      `icon-status2` no longer appears either, but it is one half of an
      alternation (`.icon-status1, .icon-status2`) and only ever appeared in one
      fixture, so there is nothing to conclude from it; it stays.
- [x] **The `values` map, checked against live pages.** Worse than the note said:
      the map is not a translation but a normaliser — each language's "no report"
      wording onto Home Assistant's `unknown`, which is what the card greys out —
      and **fourteen of the eighteen languages listed a phrase bergfex does not
      serve** (`nincs jelentés` vs `nincs üzenet`, `žádná zpráva` vs
      `žádné hlášení`, `нет данных` vs `нет сообщений`, …). Re-read off live pages
      by taking the German page of the same resort and field as the reference, so
      the phrases are evidence rather than guesses. `_translate_value` now applies
      them longest first: bergfex serves both "no info" and "no information", and
      the short one first left "unknownrmation" behind. The card's own
      `NO_REPORT_STATES` was a copy of the same wrong list and is synced.
- [x] **`operation_status` was missing in fourteen of eighteen languages.**
      bergfex labels the field differently by page — the main page carries the long
      "operating hours" label, the snow report the short one — and `const.py`
      records whichever spelling each language happened to be captured from. Only
      `at`, `it`, `se` and `pl` had recorded the short form, so everywhere else the
      alpine parser looked for a label the snow report does not print and shipped
      no status at all. Both keys are tried now. French recorded neither: its pages
      say "Heures d'ouverture", not "Ouverture". 18/18 verified live.
- [x] **Duplicate forecast images.** Sölden offered twelve daily images and ten
      summaries instead of six and five, every second one rendering "Image not
      available" and shifting the dates after it. The integration has keyed its
      entities three ways over time; where an installation carries rows from more
      than one scheme, the registry holds both and the superseded rows sit on the
      same device with nothing behind them. The registry migration declines to
      merge them on purpose — it cannot, two rows cannot share one unique id — so
      the card now ignores rows Home Assistant marks `restored` and keeps one
      image per day. This test instance has **88 orphaned image rows and 120
      orphaned sensor rows**; whether the integration should offer to delete them
      is still open (see below). Exposed a second bug on the way: the summary sort
      read `/summary_(\d+)h/`, which never matches `summary_image_48h`, so every
      id scored 0 and the sort was a no-op.
- [x] **Orphaned registry rows: a repair issue, not a silent delete.** Deleting
      registry entries is destructive - the rows carry the user's renames, their
      area assignments and their recorder history - so setup raises a repair that
      names them and counts them, and removes nothing until the user confirms the
      fix flow. A row counts as a leftover when its unique id does not start with
      the current path-based prefix, which is the one scheme the integration can
      still produce; the check is per entry, so a neighbouring resort's rows are
      never in scope. The issue clears itself once the rows are gone, however they
      went, and is persistent so a restart cannot make it look resolved. The
      card-side fix stays as it is: doing nothing remains a valid answer.

- [x] **Devices stuck on their URL slug.** Five of the ten test devices headed
      themselves `achensee`, `airolo`, `les-saisies`, `feldberg`,
      `drei-zinnen-dolomiten`. Not the parser - it resolves every one of them
      correctly today. `device_info` is read once, when the first entity
      registers, and at that moment the only name available is the one the config
      flow stored, which for an entry created while the Tailwind `tw-` breakage
      was live is the slug. The entities fix themselves on every coordinator
      update; the device never did. Setup now renames the device once the parser
      has a `resort_name`. `entry.data["name"]` is deliberately left alone -
      `legacy_unique_id_prefixes()` derives the migration prefixes from it, so
      rewriting it would strand un-migrated entities. A device the user renamed
      keeps their name, since `name_by_user` is what Home Assistant displays.
- [x] **Nothing else the season's markup broke.** The full re-fetch is the
      evidence: no field appeared that the parser does not read, and the region
      snow-report urls the coordinator builds still serve on every domain
      (`bergfex.at/tirol/`, `bergfex.fr/auvergne-rhone-alpes/`,
      `ru.bergfex.com/tirol/`, `bergfex.ch/tessin/` — all 200). All eleven entries
      in the test instance fetched successfully with no warning or error in the
      log beyond Home Assistant's standard custom-integration notice.
      One cosmetic inconsistency found and **left alone**: the cross-country
      parser keeps the page label in the resort name ("Loipenbericht Sölden",
      "Trail report 3 Zinnen Dolomites") where the alpine parser strips it. It
      predates the restyle — the winter fixture does the same — so it is not
      season drift, and changing it renames existing devices and entities.
- [x] **Close the hole that hid both of the above.** `check_live_site.py` matched
      keywords as a substring anywhere in a list of elements, while the parser
      matches a `<dt>` exactly or by prefix. The looser test passed on markup the
      parser cannot read — which is exactly how `operation` stayed broken in
      fourteen languages while the daily canary reported success. It now runs
      `parse_resort_page` itself and asserts on the fields it returns, using the
      German page of the same resort as the reference, so the check is
      seasonality-proof by construction: a block bergfex drops in summer is
      absent from the reference too and nothing is demanded of the other
      languages. Two new finding kinds, `field_missing` and `unnormalised`, fail
      the run outright. Proven both ways — exit 1 with "14 unparsed fields, 25
      unnormalised phrases" against the pre-fix code, exit 0 clean against the
      fixed one.
- [x] **Trend indicators: broken twice over, and the suite could not see it.**
      The card's test harness assigned `hass` before calling `setConfig`, which is
      the reverse of what Home Assistant does, so neither defect was reachable.
      The baseline was **never fetched on load** — Home Assistant creates the
      element, calls `setConfig`, and assigns `hass` afterwards, so the fetch in
      `setConfig` always ran with no `hass`, and `shouldUpdate` then took its early
      return because `_config` had just changed. A freshly loaded dashboard showed
      no arrows at all. Then on every later update it fetched **again**: the guard
      compared `changedProperties.get('_config')?.show_trend`, but `_config` had
      not changed, so the left side was always `undefined` and the guard always
      true — and Home Assistant hands every card a new `hass` whenever any entity
      in the instance changes. Several recorder queries a second for a number that
      moves a few times a day. Now keyed on what the answer depends on: the
      entities compared, their current values, and the hour (the 24 h window slides
      even when the page does not). Two tests drive the real order; the second
      fails with 5 recorder calls against the old code where it now expects 0.
- [x] **Snow sorting against real values: correct as it stands.** Re-tested with
      the depths bergfex served on 21 September rather than a tidy 150/100/50 —
      Hintertux 25, Sölden 22, Stubai 0, Serfaus unreported. The genuine zero sorts
      as a zero and the unreported resort goes last; a glacier with no valley row
      does not float above a resort that reported one. Recorded because nothing
      proved it before.
- [x] **Full end-to-end in `ha-bergfex-test`, with three glaciers running.**
      All eleven entries fetched successfully. Schnalstal reads **Open** (6 cm,
      2/11 lifts, season 19.09.2026 – 09.05.2027). Prices, winter and summer
      periods, operating hours, forecast images and the per-language `unknown`
      normalisation all parse — Serfaus on the Hungarian domain returns a complete
      reading. `hide_closed_resorts` hides only Airolo, Les Saisies and the
      cross-country entry, which are the genuinely between-seasons ones; the
      running glaciers stay on the card under a yellow "Summer season" badge.
- [x] **A running glacier reports `Closed`, and that stands — decided, not
      overlooked.** Hintertux on 21 September: 4 of 21 lifts, 25 cm, and two pistes
      bergfex explicitly marks open, yet the status sensor says Closed. bergfex was
      still publishing the _finished_ 2025/26 winter period (27.09.2025 –
      19.07.2026) because the new one is not announced, and `evaluate_status` reads
      that window. A pre-season glacier is not in the winter season and bergfex's
      own dates say so, so Closed is the honest answer until the published season
      starts. Nothing is hidden by it: the card still shows the depth and the lift
      counts, and the badge resolves to a yellow "Summer season" rather than a red
      "Closed", so `hide_closed_resorts` leaves the resort on the card.
      Recorded because the alternative is tempting and was weighed: `evaluate_status`
      says in its docstring that open pistes decide, while the code reads only the
      "x of y" summary row, which this page does not print. Letting `open_pistes`
      stand in would flip exactly one of the eleven test resorts — Hintertux;
      Sölden runs seven lifts on 23 cm with no piste marked open and would stay
      Closed. Rejected: it would make the sensor disagree with the season bergfex
      publishes. Pinned by
      `test_a_running_glacier_reads_closed_once_the_stale_season_is_attached`, so
      the behaviour cannot drift back without someone choosing it.

---

## Not blocking the release

- [x] Document the merged repo layout for contributors, in its own `CONTRIBUTING.md`
      rather than the README. The local AI context file is now `CLAUDE.md` and
      gitignored, so it no longer serves that purpose.

---

## Phase 2 — Ship 3.0.0 (~end Sept / early Oct)

- [ ] Tag and release; confirm HACS picks up `bergfex.zip`.
- [ ] Install matrix: clean install · upgrade from 2.3.1 · upgrade with the HACS card
      still installed · upgrade with a hand-added `/local/` resource.
- [ ] Watch the issue tracker **2–3 weeks**. Do not start Phase 3 before this settles.

---

## Phase 3 — Retire the card (mid/late Oct, gated on Phase 2)

**Order matters — remove from HACS default _before_ archiving,** or hacs/default CI
will flag the archived repo.

- [ ] Final `2.2.2` release on `lovelace-bergfex-card`: deprecation notice only.
- [ ] README banner pointing at `timmaurice/bergfex`.
- [ ] PR to `hacs/default`: remove `"timmaurice/lovelace-bergfex-card"` from `plugin`
      (line 690) and add the entry below to `removed`. `replaced` is the established
      type for this case — see `Bre77/myair`, `mattieha/slider-button-card`.

```json
{
  "repository": "timmaurice/lovelace-bergfex-card",
  "reason": "Card is now bundled with the Bergfex Snow Report integration",
  "removal_type": "replaced",
  "link": "https://github.com/timmaurice/bergfex"
}
```

- [ ] Wait for merge.
- [ ] Then archive `timmaurice/lovelace-bergfex-card`.
- [ ] Repoint any `documentation` / `issue_tracker` links that still reference the card repo.

---

## Blocked until snow returns

- Sign-off on the snow columns, trend indicators and anything driven by snow depth.
- Parser changes driven by "what the snow report looks like now".

Everything else — layout, status badges, sorting, lifts, the editor — can be checked
against the running test instance today.
