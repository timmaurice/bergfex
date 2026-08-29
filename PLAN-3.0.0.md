# Bergfex 3.0.0 — Release & Card Retirement Plan

**Goal:** ship a polished `timmaurice/bergfex` 3.0.0 that bundles the Lovelace card,
then retire `timmaurice/lovelace-bergfex-card` from HACS and archive the repo.

## Context (as of 2026-08-29)

- **No live data anywhere.** Even the Hintertux glacier snow report — the year-round
  resort — currently renders **0** `<dt>` elements; the winter fixture `hintertux.html`
  has **20**. bergfex drops the snow-report block off-season.
- Everything below marked _(offline)_ is verifiable today via the 27 HTML fixtures
  in `custom_components/bergfex/tests/fixtures/` (58 pytest + 33 vitest, all green).
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

- [ ] **B1 — Remove stale card resources on setup.**
      `custom_components/bergfex/__init__.py:92` only reconciles resources whose URL
      starts with `/bergfex_frontend/`. A user upgrading from the HACS card keeps a
      second entry (`/hacsfiles/lovelace-bergfex-card/bergfex-card.js`, or a hand-rolled
      `/local/bergfex-card.js`) and loads the bundle **twice**.
      Extend the loop to delete any resource whose URL ends in `bergfex-card.js`
      and is not `new_url`.
- [ ] **B2 — Guard the custom-element definition.**
      Both bundles use `@customElement(ELEMENT_NAME)` → `bergfex-card`
      (`frontend/src/bergfex-card.ts:63`, plus `bergfex-card-editor` in `editor.ts:39`).
      The second `customElements.define` throws at module scope, killing whichever
      copy loads second — card _and_ editor. Wrap in a `customElements.get(...)` check
      so a leftover HACS copy degrades instead of exploding.
- [ ] **B3 — Decide the migration UX.** Options: silent cleanup (B1), a repair issue
      telling the user to uninstall the HACS card, or both. Recommend B1 + repair issue.
- [ ] **B4 — Source parity check.** Diff `frontend/src/` against
      `../bergfex-card/src/` (card 2.2.1, last commit `fb516f7` "classical and skating
      trails detection") and confirm nothing was left behind in the move.

### Release hygiene _(offline)_

- [ ] Clean up stale releases on `timmaurice/bergfex`: draft `2.4.0b3`, pre-releases
      `2.4.0b2` / `2.4.0b1`. Either delete or fold their notes into 3.0.0.
- [ ] CHANGELOG for 2.3.1 → 3.0.0 (the 2.4.0 line is being skipped — say so).
- [ ] Verify `hacs.json` `zip_release` / `bergfex.zip` actually contains the built
      `bergfex-card.js`.
- [ ] Verify `.github/workflows/release.yml` runs the rollup build **before** zipping,
      so the bundle can never ship stale.
- [ ] README rewrite: one-install story, card config reference, explicit
      "migrating from lovelace-bergfex-card" section.
- [ ] Update `GEMINI.md` to describe the merged repo layout.

### Quality _(offline)_

- [ ] Card: fixture-driven visual states — loading, off-season, missing sensor,
      partial data, cross-country.
- [ ] Add a regression test for the `_getResorts()` null-guard.
- [ ] Test the "both card versions installed" path once B1/B2 land.
- [ ] **Fixture-refresh canary:** a check that flags when a live bergfex page yields
      0 `<dt>` elements _during_ the season — today off-season emptiness and a site
      redesign are indistinguishable, so a summer restructure would only surface in November.

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
- [ ] PR to `hacs/default`: - remove `"timmaurice/lovelace-bergfex-card"` from `plugin` (line 690) - add to `removed`:
      `json
{
"repository": "timmaurice/lovelace-bergfex-card",
"reason": "Card is now bundled with the Bergfex Snow Report integration",
"removal_type": "replaced",
"link": "https://github.com/timmaurice/bergfex"
}
`
      (`replaced` is the established type for this case — see `Bre77/myair`,
      `mattieha/slider-button-card`.)
- [ ] Wait for merge.
- [ ] Then archive `timmaurice/lovelace-bergfex-card`.
- [ ] Repoint any `documentation` / `issue_tracker` links that still reference the card repo.

---

## Blocked until data returns

- Any visual sign-off on a populated card.
- Parser changes driven by "what the page looks like now".
