# Milestones 0 and 1 implementation report

## Outcome

Release 0.1.0 is implemented and locally release-ready, but not published. The
repository was empty (no commits or remotes), so the required legacy tag and
branch could not be created. The two untracked legacy data files were removed
and replaced with newly downloaded, checksummed official snapshots.

## Implemented

- Standard-library runtime with one read-only generated SQLite database.
- Immutable country, code, coordinate, capital, city, geography, and source models.
- Exact lookup by names, aliases, alpha-2, alpha-3, and M49 numeric code.
- Accent-insensitive search, filtering, iteration, containment, and safe lookup.
- Twelve representative countries, twelve capitals, and 1,429 major cities.
- Separate standard-library pipeline with raw manifests, normalized JSON Lines,
  reviewed naming overrides, field provenance, validation, and deterministic builds.
- Canonical Sphinx source, API reference, generated status page, and doctests.
- Clean-wheel installation and examples executed without internet or dependencies.

## Commands executed and results

```text
python maintain.py refresh --offline   PASS
python maintain.py test                PASS (11 tests)
python maintain.py demo                PASS
python maintain.py docs                PASS (HTML -W; 5 doctests)
python maintain.py check               PASS
```

Wheel evidence:

```text
pyworldatlas-0.1.0-py3-none-any.whl
size: 91,600 bytes
runtime dependencies: 0
bundled SQLite databases: 1
```

## Source snapshots

- UN M49 overview captured 2026-07-20.
- GeoNames `countryInfo.txt` and `cities15000.zip` captured 2026-07-20.
- Each raw directory contains a SHA-256 manifest.

## Remaining release work

- Run CI across Python 3.10 through 3.14; only Python 3.12 was exercised locally.
- Configure a package remote, PyPI Trusted Publishing, and documentation deployment.
- Preserve or migrate the external legacy documentation repository, which was not
  available in this empty local repository.
- Publish the validated documentation to the existing public URL.

The later 0.2.0 through 1.0.0 roadmap milestones have not started and are not
claimed by the README or current API.
