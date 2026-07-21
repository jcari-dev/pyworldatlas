# Milestones 0 and 1 implementation report

## Outcome

Version 0.1.0 established the rebuilt runtime and generated dataset and was
tagged in the repository. The runtime and database were built from captured,
checksummed source snapshots. At this checkpoint on 2026-07-20, production PyPI
publication had not completed and the public project remained on legacy 0.0.12.

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
size: 375,654 bytes
runtime dependencies: 0
bundled SQLite databases: 1
```

## Source snapshots

- UN M49 overview captured 2026-07-20.
- GeoNames `countryInfo.txt` and `cities15000.zip` captured 2026-07-20.
- Each raw directory contains a SHA-256 manifest.

## Release evidence

- CI passed on Python 3.10 through 3.14.
- The repository contains the `v0.1.0` tag and prepared release artifacts.
- Local wheel installation returned 248 records and dataset version
  `2026.07.20`.
- Production PyPI verification failed because the public project remained on
  legacy version 0.0.12.

Reference pages:

- PyPI state checked on 2026-07-20: <https://pypi.org/project/pyworldatlas/>
- <https://github.com/jcari-dev/pyworldatlas/releases/tag/v0.1.0>
- Documentation deployment target:
  <https://jcari-dev.github.io/pyworldatlas-documentation/>

This report records the 0.1.0 baseline. Development continued in 0.2.0 with
country profile metadata, official local names, and coordinate tools.
