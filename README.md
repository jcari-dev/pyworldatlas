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

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")

    print(japan.capital.name)                  # Tokyo
    print(japan.capital.coordinates.as_tuple())
    print(atlas["DO"].name)                    # Dominican Republic
    print("France" in atlas)                   # True
```

## An honest first release

Version 0.1.0 is the clean foundation of a larger atlas. It contains twelve
representative countries generated from captured UN M49 and GeoNames sources.
It is intentionally incomplete, fully usable, and explicit about that boundary.

| Current dataset | Coverage |
|---|---:|
| Countries | 12 |
| Primary capitals | 12 |
| Capital coordinates | 12 / 12 |
| Major-city records | 1,429 |
| Runtime dependencies | 0 |
| Bundled databases | 1 SQLite file |

Later releases add geographic calculations, borders, geometry, historical
statistics, national leaders, richer country profiles, quizzes, and exports.
Those features are not presented as implemented today.

## Installation

After 0.1.0 is published to PyPI:

```console
python -m pip install pyworldatlas
```

For the current source checkout:

```console
python -m pip install -e . -e pipeline
```

The package runtime supports Python 3.10 through 3.14 during the 0.x release
series. Python versions are only claimed as release-supported after CI passes.

> **Release status:** PyPI currently serves legacy version 0.0.12. Until the
> public 0.1.0 release is completed, test this rebuild from its source checkout
> or built wheel.

## What works today

| Capability | Example |
|---|---|
| Exact lookup | `atlas.country("Japan")` |
| Standard identifiers | `atlas.country("JP")`, `atlas.country("JPN")`, `atlas.country("392")` |
| Familiar aliases | `atlas.country("USA")`, `atlas.country("Holy See")` |
| Collection behavior | `atlas["DO"]`, `"France" in atlas`, `len(atlas)` |
| Ranked search | `atlas.search_countries("united")` |
| Geographic filtering | `atlas.countries(continent="Americas")` |
| Capital records | `country.capital.name`, `.coordinates`, `.timezone_id` |
| Major cities | `atlas.major_cities("Japan", limit=5)` |
| Source inspection | `country.sources` |
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

    capital = country.capital
    print(capital.name)
    print(capital.coordinates.as_tuple())
    print(capital.population)
    print(capital.timezone_id)
```

## Search and filter

```python
with Atlas() as atlas:
    for match in atlas.search_countries("united"):
        print(match.country.name, match.matched_name, match.score)

    for country in atlas.countries(continent="Europe"):
        print(country.name, country.capital.name)
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

Raw snapshots are preserved with SHA-256 manifests. The separate builder emits
inspectable normalized JSON Lines before generating SQLite. Missing values stay
missing; country facts are never invented from model memory.

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

For this release they are `0.1.0`, `1`, and `2026.07.20` respectively.

## Documentation and roadmap

- Documentation: https://jcari-dev.github.io/pyworldatlas-documentation/
- Current implementation status: [ROADMAP_STATUS.md](ROADMAP_STATUS.md)
- Migration from the legacy API: [MIGRATION_FROM_0.0.md](MIGRATION_FROM_0.0.md)
- Milestone evidence: [MILESTONE_0_1_REPORT.md](MILESTONE_0_1_REPORT.md)

The next feature release, 0.2.0, focuses on great-circle distances, bearings,
midpoints, antipodes, destination points, and nearby-capital searches.

## License and attribution

PyWorldAtlas code is available under the [MIT License](LICENSE). GeoNames data
is provided under CC BY 4.0. Other source terms and required notices are recorded
in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
