# Bergfex 3.0.0 — Release & Card Retirement Plan

**Goal:** ship a polished `timmaurice/bergfex` 3.0.0 that bundles the Lovelace card,
then retire `timmaurice/lovelace-bergfex-card` from HACS and archive the repo.

## Context (as of 2026-08-29)

- **No live _snow_ data.** Even the Hintertux glacier snow report — the year-round
  resort — currently renders **0** `<dt>` elements; the winter fixture `hintertux.html`
  has **20**. bergfex drops the snow-report block off-season.
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
- [ ] Card: cover the two remaining degraded states, which are pure test work. - **loading** — `hass` is set but the coordinator has not delivered yet.
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
- [ ] Optional follow-up: show the winter start date on the summer badge
      ("Summer season · from 05.12."). `winter_season_start` is already on the
      sensor, so this is presentation only.

---

## Phase 1 — 18–26 Sept: first live data

- [ ] **18 Sept — Schnalstal.** First live parse of the season. Compare against fixtures.
- [ ] **26 Sept — Pitztal.** Second data point.
- [ ] **mid/late Sept — Hintertux.** Confirm the `<dt>` block is back (expect ~20).
- [ ] Refresh all 27 fixtures from live pages; commit the diff separately so parser
      drift is reviewable.
- [ ] Fix whatever the season's markup broke.
- [ ] Full end-to-end in the `ha-bergfex-test` docker instance (port 8124) with a
      real, populated resort — the first honest visual verification since spring.

---

## Not blocking the release

- [ ] Document the merged repo layout for contributors, in its own `CONTRIBUTING.md`
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
