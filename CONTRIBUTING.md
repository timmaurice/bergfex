# Contributing

This repository holds two things that ship together: a Home Assistant integration
written in Python, and the Lovelace card it serves, written in TypeScript. Until
3.0.0 the card lived in its own repository; it was merged here so the two cannot
fall out of step.

## Layout

```
custom_components/bergfex/     the integration - and the only thing users receive
  __init__.py                  setup, coordinators, Lovelace resource registration
  parser.py                    all bergfex HTML scraping
  sensor.py  image.py          entity platforms
  config_flow.py               setup and options flows
  const.py                     keywords and domains for 18 languages
  bergfex-card.js              built card, committed on purpose - see below
  translations/                integration strings, 7 languages

frontend/src/                  card sources
  bergfex-card.ts              the card
  editor.ts                    its visual editor
  types.ts                     config types and DEFAULT_CONFIG
  translation/                 card strings, 5 languages
frontend/test/                 vitest suites

tests/                         pytest suites and the bergfex HTML fixtures
scripts/                       maintenance and release tooling
```

Two things about that tree are deliberate and easy to get wrong:

**`bergfex-card.js` is a build artifact and is still committed.** The integration
serves it from disk at `/bergfex_frontend/bergfex-card.js`, so it has to exist in
a fresh checkout and inside the release archive. Rebuild it with `npm run build`
whenever you touch `frontend/src`, and commit the result alongside the source.

**`tests/` sits at the repository root, not inside the component.** The manual
install path copies `custom_components/bergfex` wholesale, and the HTML fixtures
are several megabytes. Nothing that is not shipped belongs in that directory.

## Working on the integration

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt -r requirements-test.txt
PYTHONPATH=. ./venv/bin/python -m pytest
```

Parser changes should come with a fixture. `tests/fixtures/` holds real bergfex
pages; add one rather than hand-writing HTML when the layout itself is what you
are handling.

## Working on the card

The Node version is pinned in `.nvmrc`.

```bash
npm ci
npm run build          # frontend/src -> custom_components/bergfex/bergfex-card.js
npm run test
npm run lint
npm run check-format   # npm run format writes
npm run watch          # rebuild on change
```

`DEFAULT_CONFIG` in `frontend/src/types.ts` is the single source of truth for
option defaults; the card and its editor both spread it. They used to keep
separate lists and drifted apart, so the editor showed toggles as off for options
the card was rendering. A test walks every default and asserts the editor reports
it.

## Trying it in Home Assistant

`docker-compose.yml` is not tracked (it mounts local paths). A working one:

```yaml
name: bergfex-test
services:
  homeassistant:
    container_name: ha-bergfex-test
    image: homeassistant/home-assistant:stable
    volumes:
      - ./config:/config
      - ./custom_components/bergfex:/config/custom_components/bergfex
    ports:
      - '8124:8123'
```

```bash
docker compose up -d
docker restart ha-bergfex-test   # after editing Python
```

### When the container cannot verify bergfex's certificate

Two separate things cause this, and the symptom is the same: setup fails, or the
forecast images never arrive, and the log carries a certificate verification
error such as `unable to get local issuer certificate` or
`self-signed certificate in certificate chain`.

- `vcdn.bergfex.at`, which serves the forecast images, sometimes answers without
  the intermediate certificate of its chain. A client with no cached copy of that
  intermediate cannot complete the chain on its own.
- A corporate TLS-inspecting proxy - ZScaler and its like - re-signs every
  connection with a root the container has never heard of.

The fix for both is to hand the container a CA bundle that contains what it is
missing, rather than turning verification off in the integration. Neither
`verify_ssl=False` nor a pinned certificate belongs in shipped code: users are
not behind your proxy, and a pin expires.

Build the bundle from the public roots plus the certificates your environment
needs, and mount it:

```bash
# 1. Start from the public roots - certifi's bundle, or your system's.
./venv/bin/python -c "import certifi, shutil; shutil.copy(certifi.where(), 'config/custom_cert.pem')"

# 2. Append what is missing. For the bergfex CDN, take the intermediates out of
#    the chain the server does serve - everything after the first certificate.
#    `openssl x509` would read only that first one, which is the leaf: appending
#    the server certificate supplies no issuer and expires in about 90 days.
openssl s_client -showcerts -connect vcdn.bergfex.at:443 -servername vcdn.bergfex.at </dev/null 2>/dev/null \
  | awk '/-----BEGIN CERTIFICATE-----/{n++; inc=(n>1)} inc; /-----END CERTIFICATE-----/{inc=0}' \
  >> config/custom_cert.pem

# Check what you appended before trusting it - the subject must be a CA, not
# CN=*.bergfex.at:
openssl storeutl -noout -text -certs config/custom_cert.pem | grep 'Subject:' | tail -2

# 3. Behind an inspecting proxy, append that proxy's root as well, exported from
#    the system keychain or supplied by IT.
cat zscaler-root.pem >> config/custom_cert.pem
```

Behind such a proxy step 2 hands you the proxy's own intermediates rather than
bergfex's, because the proxy is what terminated the connection - that is the same
certificate set step 3 is about, and step 2 has nothing to add. Run step 2 from a
network that is not intercepted, or skip it.

Then point the container at it, under the `homeassistant` service in
`docker-compose.yml`:

```yaml
environment:
  - SSL_CERT_FILE=/config/custom_cert.pem
  - REQUESTS_CA_BUNDLE=/config/custom_cert.pem
```

Append to the public roots - never replace them. A bundle holding only a
corporate root breaks every connection that proxy does not intercept, which is
the common trap here: bergfex starts working and everything else stops.

`config/` and `*.pem` are both gitignored, so the bundle stays local. The same
appended-bundle approach fixes `pip`, `npm` and `git` on the host behind such a
proxy; only the environment variable names differ.

The card is cached by the browser under a URL carrying the manifest version, so a
plain reload will not pick up a rebuild during development. Force one:

```js
await fetch('/bergfex_frontend/bergfex-card.js?v=3.0.0', { cache: 'reload' });
```

## Releasing

Tagging runs `.github/workflows/release.yml`, which builds the card, packs the
archive and drafts the release. `scripts/build-release-zip.mjs` refuses to build
when `manifest.json` disagrees with the tag, when a required file is missing, or
when test fixtures or caches would reach users. Check what a release would ship
before tagging:

```bash
node scripts/build-release-zip.mjs --dry-run
```

## Scraping a site that changes without notice

bergfex has no API and restructures without warning, so a few habits matter more
here than they would elsewhere.

`scripts/check_live_site.py` runs daily and validates the live markup against the
keywords in `const.py`. It fails on a keyword mismatch, on missing year-round
structure, and on a missing snow report during the winter season. Outside the
season the snow report is reported as unverifiable rather than passing silently -
bergfex removes that block every summer, and a check that cannot fail is worse
than no check.

Selectors keyed to CSS classes are fragile: bergfex dropped its Tailwind `tw-`
prefix at some point and quietly broke resort-name parsing for months, because the
winter fixtures still carried the old markup and the tests stayed green. Prefer a
structural anchor where one exists - the operating-hours panel is read through its
Alpine.js `x-show` expression, which is identical across all 18 language domains,
while the visible labels are not.

`scripts/README.md` documents the maintenance scripts.
