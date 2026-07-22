# PyWorldAtlas

> A compact, source-aware world atlas for Python that works completely offline.

[![Source 0.3.1](https://img.shields.io/badge/source-0.3.1-1677be)](CHANGELOG.md)
[![PyPI](https://img.shields.io/pypi/v/pyworldatlas.svg?label=PyPI)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-10233d)](https://www.python.org/)
[![Runtime dependencies: 0](https://img.shields.io/badge/runtime%20dependencies-0-1b8a6b)](#small-by-design)
[![Offline: yes](https://img.shields.io/badge/offline-yes-f2b84b)](#small-by-design)
[![License: MIT](https://img.shields.io/badge/license-MIT-607087)](LICENSE)

PyWorldAtlas makes real geographic data feel like ordinary Python. Look up a
country by name or code, inspect immutable country and capital objects, explore
major cities, calculate geographic relationships, and build reproducible
learning material—without an API key, runtime download, database server, or
third-party dependency.

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")

    print(japan.capital.name)                  # Tokyo
    print(japan.capital.coordinates.as_tuple())
    print(atlas["DO"].name)                    # Dominican Republic
    print("France" in atlas)                   # True
```

## Dataset coverage

The bundled dataset contains every country and area in the captured UN M49
scope, cross-checked against GeoNames country metadata. Version 0.3.0 added a
reviewed land-border graph to the profile, coordinate, capital, and
populated-place records established in earlier releases. Version 0.3.1 makes
that graph easier to query, teach, and explain.

| Current dataset | Coverage |
|---|---:|
| Countries and areas | 248 |
| Primary capitals | 241 / 248 |
| Capital coordinates | 241 / 241 |
| Populated-place records | 6,265, including retained capitals |
| Reviewed land borders | 319 undirected relationships |
| Countries and areas without an accepted land border | 85 |
| Runtime dependencies | 0 |
| Bundled databases | 1 SQLite file |

The 0.3.1 checkout includes richer country profiles, dependency-free coordinate
calculations, flag emoji, discovery cards, reproducible sampling, structured
flashcards, reviewed neighbors, and shortest land-border paths. Boundary
geometry, historical statistics, national leaders, interactive learning
applications, and exports remain later work.

## Installation

Install the latest published release:

```console
python -m pip install --upgrade pyworldatlas
```

Install the current source checkout and its separate data builder when
contributing:

```console
python -m pip install -e . -e pipeline
```

You can also test the exact local wheel after running the release build:

```console
python -m pip install --no-index --no-deps dist/pyworldatlas-0.3.1-py3-none-any.whl
```

The package runtime supports Python 3.10 through 3.14 during the 0.x release
series. Python versions are only claimed as release-supported after CI passes.

## What works in this checkout

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
| Flags and calculated facts | `country.flag_emoji`, `.population_density` |
| Discovery cards | `country.discovery_card()` |
| Stable country samples | `atlas.sample_countries(count=5, seed=42)` |
| Structured flashcards | `atlas.flashcards(topic="capitals", count=10, seed=42)` |
| City coordinates | `atlas.coordinates("Tokyo", country="JP")` |
| Distance | `atlas.distance_between("Tokyo", "Paris", first_country="JP", second_country="FR")` |
| Bearing and midpoint | `coordinate.bearing_to(other)`, `.midpoint_to(other)` |
| Land neighbors | `atlas.neighbors("France")`, `atlas.shares_border("ES", "MA")` |
| Border paths | `atlas.border_path("Portugal", "China")`, `atlas.border_crossings(...)` |
| Land connectivity | `atlas.has_land_route("Portugal", "China")` |
| Land components | `atlas.countries_reachable_by_land("Portugal")` |
| Borderless entities | `atlas.countries_with_no_land_borders()` |
| Source inspection | `country.sources` |
| Official local names | `country.local_names`, `country.name_in("pt")` |
| Serialization | `country.to_dict()`, `country.to_json()` |
| Version inspection | `atlas.dataset_info()` |

## Typed country profiles

Public results are frozen typed dataclasses rather than loosely structured
dictionaries:

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    country = atlas.country("Dominican Republic")

    print(country.name)
    print(country.official_name)
    print(country.flag)
    print(country.flag_emoji)
    print(country.codes.alpha2)
    print(country.codes.alpha3)
    print(country.codes.numeric)
    print(country.continent)
    print(country.region)
    print(country.subregion)
    print(country.area_km2)
    print(country.population)
    print(country.population_density)
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

## Country discovery and education

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")
    card = japan.discovery_card()

    print(card.flag_emoji, card.capital, card.population_density)

    for country in atlas.sample_countries(count=5, continent="Africa", seed=42):
        print(country.flag_emoji, country.name)

    for flashcard in atlas.flashcards(topic="capitals", count=3, seed=42):
        print(flashcard.prompt)
        print(flashcard.answer)
```

Sampling uses a versioned SHA-256 ranking over stable M49 identifiers, so the
same dataset, filters, and seed produce the same ordered lesson across supported
Python versions. Flashcards are immutable structured values rather than an
interactive game. Supported topics cover capitals, flags, country codes,
currencies, calling codes, domains, language codes, regions, local names,
population, area, calculated density, reviewed neighbors, and land-border
counts.

## Latitude, longitude, and distance

```python
from pyworldatlas import Atlas, Coordinate

with Atlas() as atlas:
    tokyo = atlas.city("Tokyo", country="Japan")
    paris = atlas.city("Paris", country="France")

    print(tokyo.coordinates.latitude, tokyo.coordinates.longitude)
    print(atlas.distance_between(tokyo, paris))             # kilometres
    print(atlas.distance_between(tokyo, paris, unit="mi"))  # miles
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

## Land borders and shortest paths

The land-border graph introduced in 0.3.0 contains 319 reviewed undirected
relationships. Neighbor results
are alphabetical, and equal-length shortest paths are deterministic.

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    print([country.name for country in atlas.neighbors("France")])
    print(atlas.shares_border("Spain", "Morocco"))

    path = atlas.border_path("Portugal", "China")
    print(path.crossings)
    print(" -> ".join(path.names))
    print(path.alpha2_codes)

    print(atlas.border_path("Japan", "China"))  # None
    print(atlas.has_land_route("Portugal", "China"))  # True
```

`border_path()` uses breadth-first search and returns an immutable,
JSON-serializable `BorderPathResult`. A missing route is `None`, not an error.
Maritime proximity, border geometry, border length, and road routing are not
represented.

The structured flashcard API also supports `neighbors` and `border_counts`.
Neighbor answers come directly from the reviewed graph; border counts are the
number of accepted edges attached to the selected country or area.

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

The 0.3.1 checkout uses:

- **United Nations M49** for canonical identities, standard codes, regions, and
  subregions.
- **GeoNames** for capitals, populated places, WGS84 coordinates, population
  snapshots, currencies, language and calling codes, country-code domains,
  timezone identifiers, GeoNames IDs, and one input to border review.
- **Natural Earth** public-domain 1:50m map units as an independent land-border
  topology check.

The reviewed local-name records use the **UNGEGN List of Country Names**
(``E/CONF.105/13/CRP.13``) for national official short and formal names. Current
coverage is five records across Brazil and Switzerland. The captured source
artifact and reviewed rows include checksums and exact entry/page locators.

Raw snapshots are preserved with SHA-256 manifests. The separate builder emits
inspectable normalized JSON Lines before generating SQLite. Missing values stay
missing; unsourced assumptions are never substituted for country facts.

Flag emoji are derived from alpha-2 codes, population density is a transparent
ratio of sourced values, and discovery/learning tools only rearrange existing
profile data. They introduce no additional country claims or third-party data.

The two border inputs agree on 315 relationships. Six differences have explicit
decisions in `build_data/reviewed/border_decisions.csv`: four relationships are
included and two are excluded. Any unreviewed source difference fails the data
build.

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

For this development checkout they are `0.3.1`, `3`, and `2026.07.21.1`.

## Documentation and roadmap

- Documentation source for this checkout: [docs/source](docs/source)
- Published documentation (updated by the release workflow):
  https://jcari-dev.github.io/pyworldatlas-documentation/
- Current implementation status: [ROADMAP_STATUS.md](ROADMAP_STATUS.md)
- Milestone evidence: [MILESTONE_0_1_REPORT.md](MILESTONE_0_1_REPORT.md)
- 0.2.1 execution status: [RELEASE_0_2_STATUS.md](RELEASE_0_2_STATUS.md)
- 0.3.0 release status: [RELEASE_0_3_STATUS.md](RELEASE_0_3_STATUS.md)
- 0.3.1 release status: [RELEASE_0_3_1_STATUS.md](RELEASE_0_3_1_STATUS.md)
- Maintainer release process: [RELEASING.md](RELEASING.md)

Version 0.3.1 polishes the reviewed land-border API and its learning tools.
Later releases extend boundary geometry, historical statistics, institutions,
culture, and exports.

## License and attribution

PyWorldAtlas code is available under the [MIT License](LICENSE). GeoNames data
is provided under CC BY 4.0, and Natural Earth data is public domain. Other
source terms and notices are recorded in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
