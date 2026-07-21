# Milestones 0 and 1 implementation report

## Outcome

Release 0.1.0 is implemented and publicly released through PyPI, GitHub, and the
existing documentation URL. The new runtime and database were built from
captured, checksummed official source snapshots. Legacy 0.0.x releases remain
available through PyPI's release history.

## Implemented

- Standard-library runtime with one read-only generated SQLite database.
- Immutable country, code, coordinate, capital, city, geography, and source models.
- Exact lookup by names, aliases, alpha-2, alpha-3, and M49 numeric code.
- Accent-insensitive search, filtering, iteration, containment, and safe lookup.
- 248 UN M49 countries and areas, 241 capitals, and 6,265 major cities.
- Separate standard-library pipeline with raw manifests, normalized JSON Lines,
  reviewed naming overrides, field provenance, validation, and deterministic builds.
- Canonical Sphinx source, API reference, generated status page, and doctests.
- Clean-wheel installation and examples executed without internet or dependencies.

## Commands executed and results

```text
python maintain.py refresh --offline   PASS
python maintain.py test                PASS (13 tests)
python maintain.py demo                PASS
python maintain.py docs                PASS (HTML -W; 79 doctests)
python maintain.py check               PASS
```

Wheel evidence:

```text
pyworldatlas-0.1.0-py3-none-any.whl
size: 359,011 bytes
runtime dependencies: 0
bundled SQLite databases: 1
```

## Source snapshots

- UN M49 overview captured 2026-07-20.
- GeoNames `countryInfo.txt` and `cities15000.zip` captured 2026-07-20.
- Each raw directory contains a SHA-256 manifest.

## Published release evidence

- CI passed on Python 3.10 through 3.14.
- TestPyPI and production PyPI Trusted Publishing succeeded.
- The GitHub release contains the wheel, source distribution, release manifest,
  and SHA-256 checksums.
- The canonical Sphinx output is deployed to the existing documentation URL.
- A fresh production installation returned 248 records and dataset version
  `2026.07.20`.

Release pages:

- <https://pypi.org/project/pyworldatlas/>
- <https://github.com/jcari-dev/pyworldatlas/releases/tag/v0.1.0>
- <https://jcari-dev.github.io/pyworldatlas-documentation/>

The later 0.2.0 through 1.0.0 roadmap milestones have not started and are not
claimed by the README or current API.
