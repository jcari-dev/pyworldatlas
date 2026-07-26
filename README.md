# PyWorldAtlas

> Offline country profiles, physical geography, cities, distances, and learning tools for Python.

[![PyPI](https://img.shields.io/pypi/v/pyworldatlas.svg?label=PyPI&color=287aa3)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776ab)](https://www.python.org/)
[![CI](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml/badge.svg)](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-317f78)](https://jcari-dev.github.io/pyworldatlas-documentation/)
[![License: MIT](https://img.shields.io/badge/license-MIT-607087)](LICENSE)

**248 profiles · 6,265 populated places · 319 reviewed land borders · 0 runtime dependencies**

[Documentation](https://jcari-dev.github.io/pyworldatlas-documentation/) ·
[Playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html) ·
[Five-minute tour](https://jcari-dev.github.io/pyworldatlas-documentation/explore.html) ·
[Recipes](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html) ·
[API reference](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)

> **No installation needed:** open the
> [browser playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
> and run the guided Python examples.

PyWorldAtlas turns one bundled, source-aware geographic database into ordinary
Python objects. It is designed for developers, classrooms, and curious learners
who want useful world data without an API key or runtime download.

## Install

```console
python -m pip install --upgrade pyworldatlas
```

PyWorldAtlas supports Python 3.10 through 3.14. The installed package works
offline and has no third-party runtime dependencies.

## Meet a country

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

`Atlas` opens a bundled, read-only SQLite database. Results are immutable,
typed models rather than loosely structured dictionaries, and loaded records
remain usable after the atlas is closed.

## What you can explore

| Area | Included capabilities |
|---|---|
| Country profiles | Codes, names, capitals, population, currencies, languages, timezones, postal formats, anthem titles, reviewed mottos, and demonyms |
| Names and writing systems | English identities, selected local-language names, scripts, reviewed official forms, and source-provided romanization |
| Physical geography | Land and water area, coastline, elevation extremes, rivers, lakes, and climate summaries |
| Places and measurement | 6,265 cities and capitals with coordinates, distance, initial bearing, and midpoint calculations |
| Land connections | Reviewed neighbors, shared neighbors, shortest border paths, crossings, and connected components |
| Learning tools | Stable country samples, deterministic flashcards, rankings, discovery cards, and Unicode-preserving JSON |

## Explore with small, readable programs

Look up countries by familiar name or standard code:

```python
with Atlas() as atlas:
    assert atlas.country("Japan") == atlas.country("JP")
    assert atlas.country("JPN") == atlas.country("392")
    print(atlas.country("Japan").name_in("ja"))
```

Measure and connect places:

```python
with Atlas() as atlas:
    tokyo = atlas.city("Tokyo", country="JP")
    paris = atlas.city("Paris", country="FR")

    print(f"{atlas.distance_between(tokyo, paris):,.0f} km")
    print(f"{tokyo.coordinates.bearing_to(paris.coordinates):.1f}°")

    route = atlas.border_path("Portugal", "China")
    print(" → ".join(route.names))
```

Build a repeatable lesson:

```python
with Atlas() as atlas:
    countries = atlas.sample_countries(count=5, continent="Africa", seed=42)
    cards = atlas.flashcards(topic="capitals", count=5, seed=42)

    for card in cards:
        print(card.prompt, "→", card.answer)
```

Distances are great-circle surface measurements, not road or flight routes.
Border paths use the reviewed land-border graph and do not infer maritime or
boundary geometry.

## Built for learning

- **Offline:** lessons and programs do not depend on an external service.
- **Repeatable:** seeded samples and flashcards produce stable results.
- **Source-aware:** provenance and coverage limits are documented.
- **Beginner-friendly:** common tasks use small Python objects and methods.
- **Honest about missing data:** unavailable values remain `None` or empty tuples.

The project provides factual geography and transparent calculations, not
political commentary or opinion. Read the
[educational and neutrality policy](EDUCATIONAL_AND_NEUTRALITY_POLICY.md) for
the formal publication standard.

## Coverage at a glance

Library `0.7.0` includes dataset `2026.07.22.7` and schema `7`.

| Dataset area | Coverage |
|---|---:|
| Countries and areas | 248 |
| Primary capitals | 241 / 248 |
| Populated places | 6,265 |
| Selected local-language identities | 248 / 248 |
| Anthem titles | 234 / 248 |
| Reviewed land-border relationships | 319 |
| Highest and lowest points | 240 / 248 |
| Köppen-Geiger climate profiles | 241 / 248 |

See the generated [project status](https://jcari-dev.github.io/pyworldatlas-documentation/_generated/project_status.html)
for complete coverage and [data quality](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html)
for interpretation limits.

## Data and trust

Field families use defined source roles rather than one unreviewed compilation.
The builder retains source snapshots, checksums, review decisions, and exact
coverage gates. Sources include United Nations M49, GeoNames, Unicode CLDR,
UNGEGN, Natural Earth, the CIA World Factbook, Wikidata, IANA registries, and
the Beck et al. Köppen-Geiger dataset.

- [Data sources and freshness](https://jcari-dev.github.io/pyworldatlas-documentation/data_sources.html)
- [Data quality and limitations](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html)
- [Educational purpose and editorial policy](EDUCATIONAL_AND_NEUTRALITY_POLICY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Documentation and community

- [Run Python in the browser](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
- [Browse complete recipes](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html)
- [Read the country-profile guide](https://jcari-dev.github.io/pyworldatlas-documentation/country_profile.html)
- [Explore physical geography](https://jcari-dev.github.io/pyworldatlas-documentation/physical_geography.html)
- [Review the API](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)
- [See the roadmap](ROADMAP.md)

Questions, factual corrections, documentation improvements, and focused code
contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), follow
the [code of conduct](CODE_OF_CONDUCT.md), and report security concerns through
[SECURITY.md](SECURITY.md).

## Development

```console
python maintain.py bootstrap
python maintain.py check
```

`maintain.py check` runs tests, builds both distributions, installs the wheel in
isolation, executes examples, builds strict documentation and doctests, and
audits the release contents.

## License

PyWorldAtlas code is available under the [MIT License](LICENSE). Bundled data
retains its original terms and attribution; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
