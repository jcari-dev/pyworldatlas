# PyWorldAtlas

> A compact, source-aware world atlas for Python that works completely offline.

[![Release 0.1.0](https://img.shields.io/badge/release-0.1.0-1677be)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-10233d)](https://www.python.org/)
[![Runtime dependencies: 0](https://img.shields.io/badge/runtime%20dependencies-0-1b8a6b)](#small-by-design)
[![Offline: yes](https://img.shields.io/badge/offline-yes-f2b84b)](#small-by-design)
[![License: MIT](https://img.shields.io/badge/license-MIT-607087)](LICENSE)

PyWorldAtlas makes real geographic data feel like ordinary Python. Look up a
country by name or code, inspect immutable country and capital objects, explore
major cities, search aliases, and serialize profiles—without an API key,
runtime download, database server, or third-party dependency.

> **Development checkout:** Work toward 0.2.0 is in progress. The first Country
> Discovery slice adds reviewed official local names for Brazil and Switzerland;
> the latest published PyPI release remains 0.1.0 until the release gate passes.

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")

    print(japan.capital.name)                  # Tokyo
    print(japan.capital.coordinates.as_tuple())
    print(atlas["DO"].name)                    # Dominican Republic
    print("France" in atlas)                   # True
```

## World-scale core coverage

Version 0.1.0 contains every country and area in the captured UN M49 scope,
cross-checked against GeoNames country metadata. It is broad in geographic
coverage and intentionally focused in field depth: identity, codes, regions,
area, capitals, and major cities are available now; richer data families arrive
in later releases.

| Current dataset | Coverage |
|---|---:|
| Countries and areas | 248 |
| Primary capitals | 241 / 248 |
| Capital coordinates | 241 / 241 |
| Major-city records | 6,265 |
| Runtime dependencies | 0 |
| Bundled databases | 1 SQLite file |

The 0.2.0 checkout adds richer country profiles and dependency-free coordinate
calculations. Borders, boundary geometry, historical statistics, national
leaders, quizzes, and exports remain later work.

## Installation

Install the current release from PyPI:

```console
python -m pip install pyworldatlas
```

For the current source checkout:

```console
python -m pip install -e . -e pipeline
```

The package runtime supports Python 3.10 through 3.14 during the 0.x release
series. Python versions are only claimed as release-supported after CI passes.

> **Release status:** Version 0.1.0 is published on PyPI. Legacy 0.0.x releases
> remain available in the PyPI release history for users of the former API.

## What works today

| Capability | Example |
|---|---|
| Exact lookup | `atlas.country("Japan")` |
| Standard identifiers | `atlas.country("JP")`, `atlas.country("JPN")`, `atlas.country("392")` |
| Familiar aliases | `atlas.country("USA")`, `atlas.country("Holy See")` |
| Collection behavior | `atlas["DO"]`, `"France" in atlas`, `len(atlas)` |
| Ranked search | `atlas.search_countries("united")` |
| Geographic filtering | `atlas.countries(continent="Americas")` |
| Capital records | `country.capital`, `.coordinates`, `.timezone_id` |
| Major cities | `atlas.major_cities("Japan", limit=5)` |
| Rich profile | `country.population`, `.currency`, `.languages`, `.calling_codes` |
| City coordinates | `atlas.coordinates("Tokyo", country="JP")` |
| Distance | `atlas.distance_between("Tokyo", "Paris", first_country="JP", second_country="FR")` |
| Bearing and midpoint | `coordinate.bearing_to(other)`, `.midpoint_to(other)` |
| Source inspection | `country.sources` |
| Official local names | `country.local_names`, `country.name_in("pt")` |
| Serialization | `country.to_dict()`, `country.to_json()` |
| Version inspection | `atlas.dataset_info()` |

## Country profiles with autocomplete

Public results are frozen typed dataclasses rather than loosely structured
dictionaries:

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    country = atlas.country("Dominican Republic")

    print(country.name)
    print(country.official_name)
    print(country.flag)
    print(country.codes.alpha2)
    print(country.codes.alpha3)
    print(country.codes.numeric)
    print(country.continent)
    print(country.region)
    print(country.subregion)
    print(country.area_km2)
    print(country.population)
    print(country.currency)
    print(country.languages)
    print(country.calling_codes)
    print(country.top_level_domain)
    print(country.observed_timezones)

    if country.capital is not None:
        print(country.capital.name)
        print(country.capital.coordinates.as_tuple())
        print(country.capital.population)
        print(country.capital.timezone_id)
```

## Latitude, longitude, and distance

```python
from pyworldatlas import Atlas, Coordinate

with Atlas() as atlas:
    tokyo = atlas.city("Tokyo", country="Japan")
    paris = atlas.city("Paris", country="France")

    print(tokyo.coordinates.latitude, tokyo.coordinates.longitude)
    print(atlas.distance_between(tokyo, paris))             # kilometres
    print(atlas.distance_between(tokyo, paris, unit="mi")) # miles
    print(tokyo.coordinates.bearing_to(paris.coordinates))
    print(tokyo.coordinates.midpoint_to(paris.coordinates))

london = Coordinate(51.5074, -0.1278)
paris_center = Coordinate(48.8566, 2.3522)
print(london.distance_to(paris_center))
```

Distances use the haversine formula and WGS84 mean Earth radius. They are
surface great-circle distances, not road or flight-routing distances.

## Search and filter

```python
with Atlas() as atlas:
    for match in atlas.search_countries("united"):
        print(match.country.name, match.matched_name, match.score)

    for country in atlas.countries(continent="Europe"):
        capital = country.capital.name if country.capital else "not available"
        print(country.name, capital)
```

Search is case- and accent-insensitive. Exact country lookup accepts common
names, reviewed aliases, alpha-2, alpha-3, and M49 numeric codes.

## Test every current record in VS Code

The repository includes a deliberately rich [playground.py](playground.py). It
validates every current country, capital, and city record before demonstrating
the complete implemented API.

Press `F5` in VS Code and select **PyWorldAtlas: Full Playground**, or run:

```console
python playground.py
```

Focused modes:

```console
python playground.py --audit-only
python playground.py --country Japan
python playground.py --json "Dominican Republic"
python playground.py --country "United States" --all-cities
```

The playground runs directly from a repository checkout even before an editable
installation. Normal applications should install the package.

## Small by design

The installed wheel contains only:

- Python source files.
- One generated, read-only SQLite database.
- Standard package metadata.

At runtime PyWorldAtlas does not:

- Contact the internet.
- Require an API key.
- Download or decompress data after installation.
- Write into `site-packages`.
- Load the complete database during `Atlas()` initialization.
- Depend on pandas, NumPy, an ORM, a GIS engine, or SQLite extensions.

## Data you can trace

Release 0.1.0 uses:

- **United Nations M49** for canonical identities, standard codes, regions, and
  subregions.
- **GeoNames** for capitals, major cities, WGS84 coordinates, population
  snapshots, timezone identifiers, and GeoNames IDs.

The 0.2.0 development pilot additionally uses the approved **UNGEGN List of
Country Names** (``E/CONF.105/13/CRP.13``) for national official short and
formal names. The captured source artifact and reviewed rows include checksums
and exact entry/page locators.

Raw snapshots are preserved with SHA-256 manifests. The separate builder emits
inspectable normalized JSON Lines before generating SQLite. Missing values stay
missing; unsourced assumptions are never substituted for country facts.

Seven areas have no usable primary-capital record in the current snapshot.
Their `country.capital` value is `None`. GeoNames-only country rows that do
not have a matching identity in the captured UN M49 scope are excluded rather
than inferred.

See [DATA_SOURCES.md](DATA_SOURCES.md), [DATA_QUALITY.md](DATA_QUALITY.md), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Three different versions

```python
with Atlas() as atlas:
    print(atlas.dataset_info())
```

- **Library version** describes Python behavior and the public API.
- **Schema version** describes compatibility with the bundled SQLite structure.
- **Dataset version** identifies the captured source snapshot.

For this development checkout they are `0.2.0`, `2`, and `2026.07.20.1`.

## Documentation and roadmap

- Documentation: https://jcari-dev.github.io/pyworldatlas-documentation/
- Current implementation status: [ROADMAP_STATUS.md](ROADMAP_STATUS.md)
- Migration from the legacy API: [MIGRATION_FROM_0.0.md](MIGRATION_FROM_0.0.md)
- Milestone evidence: [MILESTONE_0_1_REPORT.md](MILESTONE_0_1_REPORT.md)
- 0.2.0 execution status: [RELEASE_0_2_STATUS.md](RELEASE_0_2_STATUS.md)
- Maintainer release process: [RELEASING.md](RELEASING.md)

The next feature release, 0.2.0, follows the Country Discovery sequence:
official local names, deterministic sampling and flags, reviewed borders and
paths, then sourced discovery cards and flashcards.

## License and attribution

PyWorldAtlas code is available under the [MIT License](LICENSE). GeoNames data
is provided under CC BY 4.0. Other source terms and required notices are recorded
in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
