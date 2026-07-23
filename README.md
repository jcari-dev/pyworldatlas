# PyWorldAtlas

> Offline country profiles, physical geography, and geographic tools for Python.

[![PyPI](https://img.shields.io/pypi/v/pyworldatlas.svg?label=PyPI&color=287aa3)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776ab)](https://www.python.org/)
[![CI](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml/badge.svg)](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-317f78)](https://jcari-dev.github.io/pyworldatlas-documentation/)
[![Playground](https://img.shields.io/badge/playground-run%20Python-9a762f)](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
[![License: MIT](https://img.shields.io/badge/license-MIT-607087)](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE)

PyWorldAtlas turns a bundled, source-aware geographic database into ordinary
Python objects. Explore names and writing systems, capitals and cities,
physical geography, climate classes, coordinates, distances, reviewed land
neighbors, rankings, and learning tools without an API key or runtime download.

**248 profiles · 6,265 populated places · 319 reviewed land borders · 0 runtime dependencies**

[Documentation](https://jcari-dev.github.io/pyworldatlas-documentation/) ·
[Playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html) ·
[Five-minute tour](https://jcari-dev.github.io/pyworldatlas-documentation/explore.html) ·
[API reference](https://jcari-dev.github.io/pyworldatlas-documentation/api.html) ·
[Data sources](https://jcari-dev.github.io/pyworldatlas-documentation/data_sources.html) ·
[Changelog](https://jcari-dev.github.io/pyworldatlas-documentation/changelog.html)

## Installation

```console
python -m pip install --upgrade pyworldatlas
```

PyWorldAtlas supports Python 3.10 through 3.14. The installed package has no
third-party runtime dependencies and does not require network access.

## A quick country postcard

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    brazil = atlas.country("Brazil")

    print(brazil.flag, brazil.name_in("pt"), "—", brazil.capital.name)
    print(brazil.highest_point.name, f"{brazil.highest_point.elevation_m:,.0f} m")
    print(", ".join(river.name for river in brazil.rivers[:3]))
    print(brazil.climate.dominant_zone.code, brazil.climate.dominant_zone.name)
```

```text
🇧🇷 Brasil — Brasília
Pico da Neblina 2,994 m
Amazon, Río de la Plata/Paraná, Tocantins
Aw Tropical, savannah
```

`Atlas` opens one bundled, read-only SQLite database. Results are immutable
typed models rather than loosely structured dictionaries, and materialized
records remain usable after the atlas is closed.

## What can you explore?

| Area | Included capabilities |
|---|---|
| Country profiles | Standard codes, names, capitals, population, currencies, languages, timezones, postal formats, anthem titles, reviewed mottos, and demonyms |
| Names and writing systems | English identities, selected local-language names, scripts, reviewed official forms, and source-provided romanization |
| Physical geography | Land and water area, coastline, elevation extremes, mean elevation, source-listed rivers and lakes, and climate summaries |
| Climate | Represented 1991–2020 Köppen-Geiger classes, dominant zones, and country-level shares |
| Places and measurement | 6,265 coordinate-bearing places, great-circle distance, initial bearing, and spherical midpoint |
| Land connections | Reviewed neighbors, shared neighbors, shortest border paths, crossings, connected components, and borderless profiles |
| Discovery | Exact filters, rankings, nearby capitals, feature search, stable samples, discovery cards, and flashcards |
| Data use | Dictionary and JSON serialization with Unicode and source context preserved |

## Rich, source-aware profiles

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("JP")

    print(japan.name, japan.formal_name, japan.flag)
    print(japan.name_in("ja"), japan.local_name("ja").script_code)
    print(japan.anthem.title)
    print(japan.demonym.noun, japan.demonym.adjective)
    print(japan.currency.name, japan.currency.symbol)
    print(japan.timezone_ids)
    print([source.id for source in japan.sources])
```

Common names, aliases, ISO alpha-2 and alpha-3 identifiers, and M49 numeric
codes all resolve through the same lookup API:

```python
with Atlas() as atlas:
    assert atlas.country("Japan") == atlas.country("JP")
    assert atlas.country("JPN") == atlas.country("392")
    assert atlas.country("usa").name == "United States"
```

Missing source values remain explicit: optional scalars use `None`, and
unavailable collections are empty tuples. PyWorldAtlas does not manufacture
values to make a profile appear complete.

## Measure and connect places

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    tokyo = atlas.city("Tokyo", country="JP")
    paris = atlas.city("Paris", country="FR")

    print(atlas.distance_between(tokyo, paris))
    print(tokyo.coordinates.bearing_to(paris.coordinates))
    print(tokyo.coordinates.midpoint_to(paris.coordinates))

    route = atlas.border_path("Portugal", "China")
    print(route.crossings)
    print(" → ".join(route.names))
```

Distance calculations use a WGS84 mean Earth radius and the haversine formula.
They describe great-circle surface distance, not road or flight routing.
Land-border paths use the reviewed undirected border graph; maritime proximity
and boundary geometry are not inferred.

## Discover, compare, and learn

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    longest_coastlines = atlas.rank("coastline", limit=5)
    nearby = atlas.nearest_capitals("Tokyo", country="JP", limit=5)
    amazon_profiles = atlas.countries_with_river("Amazon")

    sample = atlas.sample_countries(count=5, continent="Africa", seed=42)
    cards = atlas.flashcards(topic="capitals", count=3, seed=42)
```

Rankings only order labelled sourced values or transparent calculations; they
do not score countries or people. Sampling and flashcards use stable,
versioned ordering so the same package version, filters, and seed produce the
same lesson on every supported Python version.

## Coverage snapshot

Dataset version `2026.07.22.7` ships with library version `0.7.0` and schema
version `7`.

| Dataset area | Coverage |
|---|---:|
| Countries and areas | 248 |
| Primary capitals | 241 / 248 |
| Populated places | 6,265 |
| Selected local-language identities | 248 / 248, across 80 languages and 21 scripts |
| Sourced English formal names | 240 / 248 |
| Anthem titles | 234 / 248 |
| Reviewed source-listed mottos | 32 / 248 |
| English demonym profiles | 227 / 248 |
| Reviewed land-border relationships | 319 |
| Land area and coastline | 238 / 248 each |
| Highest and lowest points | 240 / 248 each |
| Source-listed rivers | 188 records across 80 profiles |
| Source-listed lakes | 187 records across 69 profiles |
| Köppen-Geiger climate profiles | 241 / 248 |

The complete, generated coverage report is available in the
[project status](https://jcari-dev.github.io/pyworldatlas-documentation/_generated/project_status.html)
and the exact limitations are documented in
[Data quality](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html).

## Flags and local names

`Country.flag` and `Country.flag_emoji` return the same Unicode
regional-indicator sequence derived from the profile's alpha-2 code. Rendering
depends on the operating system, terminal, browser, and font; some environments
display two regional-indicator letters instead of flag artwork.

Every profile includes one selected, sourced local identity. Local names remain
ordinary Unicode strings, so Arabic, Chinese, Cyrillic, Devanagari, Japanese,
and Latin writing systems work offline without a translation service. Evidence
kinds distinguish a locale display name from a reviewed national official
form. See [Local names and writing systems](https://jcari-dev.github.io/pyworldatlas-documentation/local_names.html)
for the exact contract.

## Data and trust

PyWorldAtlas is an educational and reference package. It provides factual
geography and transparent calculations, not political commentary or opinion.
Each field family has a documented source role, validation boundary, and
missing-data policy.

The current dataset uses narrowly defined fields from established sources,
including United Nations M49, GeoNames, Unicode CLDR, UNGEGN, Natural Earth,
the CIA World Factbook, Wikidata, IANA registries, and the Beck et al.
Köppen-Geiger dataset. Source snapshots, versions, checksums, review decisions,
and exact coverage gates are retained by the builder.

- [Educational purpose and editorial policy](https://github.com/jcari-dev/pyworldatlas/blob/main/EDUCATIONAL_AND_NEUTRALITY_POLICY.md)
- [Data sources and freshness](https://jcari-dev.github.io/pyworldatlas-documentation/data_sources.html)
- [Data quality and limitations](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html)
- [Third-party notices](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md)

## Small by design

The installed wheel contains Python source, package metadata, and one generated
read-only SQLite database. At runtime it does not:

- contact the internet or require an API key;
- download or decompress data;
- write into `site-packages`;
- load every profile during `Atlas()` initialization; or
- depend on pandas, NumPy, an ORM, a GIS engine, or SQLite extensions.

## Documentation

The documentation includes executable examples, interpretation notes, coverage
boundaries, source provenance, and the complete public API.

- [Run Python in the browser](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
- [Python recipe gallery](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html)
- [Explore the atlas in five minutes](https://jcari-dev.github.io/pyworldatlas-documentation/explore.html)
- [60-second quickstart](https://jcari-dev.github.io/pyworldatlas-documentation/quickstart.html)
- [Country profiles](https://jcari-dev.github.io/pyworldatlas-documentation/country_profile.html)
- [Physical geography](https://jcari-dev.github.io/pyworldatlas-documentation/physical_geography.html)
- [Coordinates and distances](https://jcari-dev.github.io/pyworldatlas-documentation/coordinates_distances.html)
- [Land borders and paths](https://jcari-dev.github.io/pyworldatlas-documentation/borders.html)
- [API reference](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)

## Development

Install the runtime, builder, and documentation tools from a source checkout:

```console
python -m pip install -e . -e pipeline -r docs/requirements.txt
python maintain.py check
```

`maintain.py check` runs the runtime and pipeline tests, builds both package
distributions, installs the wheel in isolation, executes examples, builds
strict documentation and doctests, and audits release contents.

Factual corrections and focused contributions are welcome. Read the
[contribution guide](https://github.com/jcari-dev/pyworldatlas/blob/main/CONTRIBUTING.md)
and [code of conduct](https://github.com/jcari-dev/pyworldatlas/blob/main/CODE_OF_CONDUCT.md)
before opening a pull request.

## Versioning

PyWorldAtlas tracks three separate versions:

- **Library version** describes Python behavior and the public API.
- **Schema version** describes compatibility with the bundled SQLite structure.
- **Dataset version** identifies the captured source snapshot.

Inspect all three with `atlas.dataset_info()`.

## License

PyWorldAtlas code is available under the
[MIT License](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE).
Bundled data retains its original terms and attribution; see
[THIRD_PARTY_NOTICES.md](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md)
for details.
