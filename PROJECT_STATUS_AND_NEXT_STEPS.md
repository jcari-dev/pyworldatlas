# PyWorldAtlas maintainer handoff and completion plan

## Purpose

This is the canonical human-facing handoff for continuing PyWorldAtlas after
the successful 0.1.0 rebuild. It records what is public, how the repository is
organized, what remains incomplete, and the recommended order for reaching the
stable 1.0.0 goal.

Use this document to begin a new work session. Use `RELEASING.md` for the exact
release procedure and `ROADMAP_STATUS.md` for generated milestone evidence.

## Executive status

PyWorldAtlas 0.1.0 is a complete and publicly usable first rebuild release. It
is an offline, dependency-free Python package containing typed runtime models
and one generated SQLite database. The release covers 248 UN M49 countries and
areas, 241 primary capitals, and 6,265 major cities.

The foundation is complete. The broader atlas described by the roadmap is not:
geographic calculations, borders, geometry, historical statistics, leaders,
richer profiles, and educational tools remain future milestones.

### Public release evidence

| Surface | Current state | Evidence |
|---|---|---|
| Library | 0.1.0 | <https://pypi.org/project/pyworldatlas/> |
| Source | `main` | <https://github.com/jcari-dev/pyworldatlas> |
| Release | `v0.1.0` with four assets | <https://github.com/jcari-dev/pyworldatlas/releases/tag/v0.1.0> |
| Documentation | 0.1.0 live | <https://jcari-dev.github.io/pyworldatlas-documentation/> |
| Dataset | 2026.07.20 | `build_data/reports/status.json` |
| Schema | 1 | `src/pyworldatlas/_version.py` |
| Supported Python | 3.10 through 3.14 | GitHub Actions CI matrix |
| Runtime dependencies | 0 | `pyproject.toml` and wheel audit |

The production wheel was installed into a fresh environment and returned:

```text
248 Mexico City 0.1.0 2026.07.20
```

## What 0.1.0 delivered

### Runtime and public API

- Dependency-free runtime using only the Python standard library.
- One bundled, read-only SQLite database.
- Immutable dataclass models for countries, codes, coordinates, geography,
  capitals, cities, localized names, source references, and dataset metadata.
- Country lookup by common name, alias, alpha-2, alpha-3, and M49 code.
- Accent-insensitive ranked search and continent/region filtering.
- Collection behavior: iteration, length, containment, indexing, and safe lookup.
- Capital and major-city access.
- Dictionary and JSON serialization.
- Independent library, schema, and dataset version reporting.
- No runtime network access, API key, database server, ORM, or import-time output.

### Data and pipeline

- 248 countries and areas from a captured UN M49 snapshot.
- 241 primary capitals with coordinates.
- 6,265 GeoNames major-city records.
- Checksummed raw snapshots under `build_data/raw/`.
- Separate builder project under `pipeline/`.
- Reviewed naming overrides and per-field source mapping.
- Deterministic ordering, validation, SQLite integrity checks, and a reproducible
  database test.
- Inspectable coverage and status reports.

### Developer experience and documentation

- `playground.py` audits every record and demonstrates the complete current API.
- Focused examples under `examples/`.
- Sphinx documentation built from the installed release wheel.
- 79 passing doctests and warnings-as-errors HTML builds.
- Conventional Python documentation theme and preserved public docs URL.
- Migration guide from the incompatible 0.0.x prototype.

### Packaging and operations

- Standard wheel and source distribution.
- CI on Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- TestPyPI rehearsal workflow.
- PyPI Trusted Publishing with short-lived OIDC credentials.
- Tag-driven production publication.
- Release manifest and SHA-256 checksums.
- Automated deployment to `jcari-dev/pyworldatlas-documentation`.

## Repository map and ownership

| Path | Purpose | Edit policy |
|---|---|---|
| `src/pyworldatlas/` | Public runtime and models | Hand-edit code; never place builder dependencies here |
| `src/pyworldatlas/data/atlas.sqlite3` | Installed generated database | Never edit manually; rebuild through the pipeline |
| `pipeline/` | Source ingestion, normalization, validation, and SQLite generation | Builder-only code and dependencies |
| `build_data/raw/` | Immutable captured source snapshots | Add new dated snapshots; never rewrite old snapshots |
| `build_data/normalized/` | Inspectable normalized intermediates | Generated and ignored |
| `build_data/reports/` | Coverage, status, logs, and review outputs | Generate from pipeline truth |
| `docs/source/` | Canonical Sphinx source | Hand-edit source; never edit deployed HTML |
| `docs/_build/` | Local generated documentation | Generated and ignored |
| `tests/` | Runtime, import, playground, and pipeline verification | Expand with every feature/data family |
| `playground.py` | Human-facing full API and data audit | Keep current with every public capability |
| `maintain.py` | Maintainer command entry point | Keep normal workflows discoverable and numbered |
| `.github/workflows/` | CI, TestPyPI, production release, docs deployment | Treat as release-critical code |
| `build_data/reports/status.json` | Canonical generated milestone status | Change its generator, then regenerate |
| `ROADMAP_STATUS.md` | Human-readable generated status | Never hand-edit |

The intended build and release flow is:

```text
captured sources
    -> normalization and reviewed overrides
    -> validation and reports
    -> generated SQLite
    -> runtime tests and wheel
    -> examples and Sphinx from that wheel
    -> version tag
    -> PyPI + GitHub Release + documentation deployment
```

## Current quality baseline

The following must remain true after every change:

- `python maintain.py test` passes.
- `python maintain.py check` passes.
- The wheel contains one SQLite database and excludes pipeline, tests, docs, and
  raw/build data.
- Every example runs against a clean wheel installation.
- Sphinx HTML and doctests pass with warnings treated as errors.
- Runtime imports remain standard-library-only.
- Missing values remain explicit; no unsourced fact is introduced.
- README and public docs describe only released behavior.

## Known limitations and remaining operational work

### Product limitations

- Seven areas have no usable primary-capital record and correctly return `None`.
- 0.1.0 is broad in identity coverage but intentionally shallow in profile depth.
- There are no distance, bearing, nearby-place, border, geometry, statistics,
  leader, quiz, or general export APIs yet.
- Country classification remains conservative where sources do not support a
  more precise value.
- Major cities use the GeoNames `cities15000` scope rather than every settlement.

### Pipeline and release limitations

- The current canonical rebuild is offline from captured snapshots. Online
  source fetching and selective refresh commands are not implemented yet.
- Documentation deployment uses a fine-grained repository token. Keep it scoped
  only to `pyworldatlas-documentation` with Contents read/write access.
- Sphinx doctests run, but a release link-check gate has not been added.
- Automated scheduled data-refresh pull requests, performance reports, and
  wheel-size regression gates remain future hardening work.
- The 0.1.0 GitHub Release page required a one-time manual recovery. The workflow
  was corrected on `main` in commit `bab1dbf` for future releases.

## Immediate post-0.1.0 housekeeping

Complete these before or alongside 0.2.0 development:

- [ ] Protect `main` and require the CI quality gate for pull requests.
- [ ] Add the documentation URL, PyPI URL, description, and relevant topics to
      the GitHub repository About section.
- [ ] Confirm the `pypi` environment requires maintainer approval.
- [ ] Record a rotation/recovery procedure for `DOCS_DEPLOY_TOKEN` without
      storing the token in repository files.
- [ ] Add a Sphinx `linkcheck` job and decide which external-link failures may be
      retried or allowlisted.
- [ ] Add basic import/lookup timing and wheel-size reports before features make
      the package substantially larger.
- [ ] Open one issue per 0.2.0 workstream rather than developing the release as
      one unreviewable change.

## Next release: 0.2.0 offline geographic calculations

### Release promise

Version 0.2.0 should make the existing coordinates useful without adding any
runtime dependency. Users should be able to calculate great-circle distance,
bearing, midpoint, antipode, destination points, and nearby capitals/cities
entirely offline.

### Recommended implementation sequence

#### 1. Freeze the public contracts

Define typed models and exceptions before implementing formulas:

- `PlaceReference`
- `DistanceResult`
- unit normalization for `km`, `mi`, and `nm`
- `InvalidUnitError`
- explicit ambiguous/unknown place behavior

Decide how `Coordinate`, `Capital`, `City`, and `(city, country)` inputs resolve.
Do not let a plain country string silently mean either capital or centroid.

#### 2. Build the pure geographic math layer

Add a private, standard-library-only module for:

- Haversine great-circle distance.
- Initial bearing and compass direction.
- Great-circle midpoint.
- Antipode.
- Destination point from distance and bearing.
- Distance to the equator and prime meridian.

Centralize the documented mean Earth radius and unit conversions. Keep math
functions independent from SQLite so they can be tested exhaustively.

#### 3. Add reliable place resolution

Before city-to-city calculations, add or complete:

- Exact city lookup with country disambiguation.
- Ranked city search.
- Deterministic handling of duplicate city names.
- Conversion of supported public objects into coordinates and references.

Ambiguous city strings must return ranked choices or raise a documented error;
they must never select an arbitrary row.

#### 4. Add Atlas navigation methods

Implement the roadmap surface:

- `distance()`
- `distance_between_capitals()`
- `distance_between_cities()`
- `bearing()`
- `midpoint()`
- `antipode()`
- `destination_point()`
- `distance_to_equator()`
- `distance_to_prime_meridian()`
- `nearest_capitals()` and `capitals_within()`
- `nearest_cities()` and `cities_within()`

Order equal-distance results deterministically by country code and place name.
Document that distances are straight-line surface distances, not routes.

#### 5. Test from formulas through the installed wheel

Add tests for:

- Identical and antipodal coordinates.
- International Date Line and pole-adjacent cases.
- Known city/capital fixture distances with explicit tolerances.
- Unit aliases and invalid units.
- Ambiguous place names.
- Stable nearby-result ordering.
- Empty/missing-capital behavior.
- Context-manager and closed-atlas behavior for new methods.
- All new public examples through `playground.py` and doctests.

#### 6. Document the feature as part of implementation

Add a geography tutorial, complete API reference entries, interpretation/units
notes, and runnable examples. Update the README only when the complete feature
is merged and tested.

#### 7. Release 0.2.0 through the established pipeline

Update the four version/changelog locations, regenerate status, run TestPyPI,
and publish `v0.2.0` only after the full gate passes.

### 0.2.0 definition of done

- [ ] All advertised calculation and nearby-search methods are implemented.
- [ ] Runtime remains standard-library-only.
- [ ] Numeric edge cases and trusted fixtures pass.
- [ ] Ambiguous place resolution is deterministic and documented.
- [ ] `playground.py` demonstrates every new public method.
- [ ] README and Sphinx geography examples run against the wheel.
- [ ] Python 3.10 through 3.14 CI is green.
- [ ] TestPyPI installation succeeds in a clean environment.
- [ ] Production PyPI, GitHub Release, and docs publish from one tag.
- [ ] `ROADMAP_STATUS.md` marks 0.2.0 released only after public verification.

## Remaining release train

| Version | Outcome | Principal new source/work | Exit gate |
|---|---|---|---|
| 0.3.0 | Borders and relationships | Border dataset ingestion and graph algorithms | Symmetry, islands, and no-path cases validated |
| 0.4.0 | Country geometry | Natural Earth geometry, compression, pure-Python containment | Lazy loading, package-size report, dispute caveats |
| 0.5.0 | Historical statistics | Reviewed World Bank indicator allowlist | Every value has year, unit, source, and missing-data rules |
| 0.6.0 | Top national leaders | CIA World Leaders normalization | Titles reviewed; freshness and coverage visible |
| 0.7.0 | Rich country profiles | Names, languages, currencies, timezones, communications, culture | Optional enrichment is sourced and never blocks core records |
| 0.8.0 | Education and export | Quizzes, facts, CLI, JSON/JSONL/CSV/GeoJSON | Seeded behavior deterministic; exports tested |
| 0.9.0 | Full-world hardening | Refresh automation, diff reports, performance, link checking | Repeated package-and-doc releases without manual artifact editing |
| 1.0.0 | Stable offline atlas | API stabilization and complete migration guidance | API proven across 0.x; refresh/release operations repeat reliably |

## Normal maintainer workflow

From a VS Code terminal:

```console
python maintain.py bootstrap
python maintain.py status
python maintain.py test
python playground.py
python maintain.py check
python maintain.py preview
```

`preview` serves the current documentation at `http://127.0.0.1:8000/` until
Ctrl+C is pressed.

For the current captured dataset, rebuild offline with:

```console
python maintain.py refresh --offline
python maintain.py status
python maintain.py check
```

Review `build_data/reports/` and the SQLite checksum after every data rebuild.
Never edit the generated database to correct a record; fix the source adapter,
normalization rule, or reviewed override and regenerate it.

## Feature completion checklist

A feature is complete only when all of the following are true:

- [ ] Public API and failure behavior are documented.
- [ ] Implementation uses only allowed runtime dependencies.
- [ ] Unit and integration tests cover normal, missing, ambiguous, and closed
      database behavior.
- [ ] Pipeline validation and provenance are updated for any new data fields.
- [ ] `playground.py` and examples expose the new behavior.
- [ ] Sphinx source, API docs, and doctests are updated in the same change.
- [ ] `python maintain.py check` passes.
- [ ] Generated status reflects reality.
- [ ] The README does not claim the feature before release.

## Release checklist for every version

1. Update `pyproject.toml`, `src/pyworldatlas/_version.py`,
   `docs/source/conf.py`, and `CHANGELOG.md` together.
2. Regenerate data/status artifacts when coverage or milestone state changes.
3. Run `python maintain.py prepare-release VERSION`.
4. Review `dist/release-manifest.json` and `dist/SHA256SUMS`.
5. Commit the release state and wait for green CI.
6. Run the TestPyPI workflow and install that exact version cleanly.
7. Create an annotated `vVERSION` tag and push it.
8. Approve the protected `pypi` environment if prompted.
9. Verify PyPI metadata and install the production wheel cleanly.
10. Verify GitHub Release assets and the public documentation version.
11. Mark the milestone `released` only after all public surfaces are verified.

Never reuse or move a published version tag. PyPI versions and release tags are
immutable release records.

## Versioning rules

- Feature/API addition: next planned minor release, such as 0.2.0.
- Data refresh without API change: patch release, such as 0.2.1.
- Compatible bug or documentation fix: patch release.
- Incompatible schema change: increment schema version and document migration.
- Dataset refresh: update dataset version independently using `YYYY.MM.DD`.

## Non-negotiable project rules

- Runtime remains standard-library-only and offline.
- One generated SQLite database ships in the wheel.
- Raw source snapshots are immutable and checksummed.
- Missing data is acceptable; unsourced data is not.
- Every final field is traceable to a source or reviewed override.
- Generated SQLite and deployed HTML are never manually patched.
- Political and boundary conventions are documented explicitly.
- New runtime dependencies, web services, GUIs, and live-data behavior remain out
  of scope unless the roadmap is deliberately revised.
- Every milestone remains installable, testable, documented, and honestly scoped.

## Recommended next session

Begin 0.2.0 with one narrow design-and-test slice:

1. Create a feature branch.
2. Add unit normalization, `PlaceReference`, `DistanceResult`, and exceptions.
3. Add pure Haversine distance and bearing functions with trusted fixtures.
4. Expose `distance_between_capitals()` only after the underlying contracts pass.
5. Update `playground.py` and add the first geography doctest.
6. Run `python maintain.py check` before expanding to nearby searches.

This produces a reviewable first increment while protecting the simplicity that
0.1.0 established.
