# PyWorldAtlas: offline world geography for Python

> Offline country profiles, physical geography, optional 3D maps, distances, and learning tools for Python.

[![PyPI](https://img.shields.io/pypi/v/pyworldatlas.svg?label=PyPI&color=287aa3)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776ab)](https://www.python.org/)
[![CI](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml/badge.svg)](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-317f78)](https://jcari-dev.github.io/pyworldatlas-documentation/)
[![License: MIT](https://img.shields.io/badge/license-MIT-607087)](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE)

**248 profiles · 248 optional 3D maps · 6,265 populated places · 0 core runtime dependencies**

[Documentation](https://jcari-dev.github.io/pyworldatlas-documentation/) ·
[Quickstart](https://jcari-dev.github.io/pyworldatlas-documentation/quickstart.html) ·
[Playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html) ·
[3D maps](https://jcari-dev.github.io/pyworldatlas-documentation/maps.html) ·
[Examples](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html) ·
[API reference](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)

> **No installation needed:** open the
> [browser playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
> and run the guided Python examples.

PyWorldAtlas is an offline world-geography Python package built around one
bundled, source-aware database. It turns country profiles, physical geography,
cities, distances, borders, optional 3D maps, and learning tools into ordinary
Python objects for developers, classrooms, and curious learners. No API key is
required, and installed features work offline.

[![PyWorldAtlas Standard 3D elevation map of Iceland](https://raw.githubusercontent.com/jcari-dev/pyworldatlas/main/docs/source/_static/iceland-standard-map.svg)](https://jcari-dev.github.io/pyworldatlas-documentation/maps.html)

*Iceland rendered by the Standard map edition with elevation, coastline,
Reykjavík, a river overlay, and source notes. Select the image for the map
guide.*

## Install

```console
python -m pip install --upgrade pyworldatlas
```

PyWorldAtlas supports Python 3.10 through 3.14. The installed package works
offline and has no third-party runtime dependencies.

Add the recommended global 3D map edition when you want interactive terrain:

```console
python -m pip install --upgrade "pyworldatlas[maps]"
```

Use `pyworldatlas[maps-overview]` for the smaller Overview edition. Map data is
optional and never enlarges the ordinary package installation.

## Meet a country

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    brazil = atlas.country("Brazil")
    print(brazil.summary())
```

```text
🇧🇷 Brazil · Brasil
Formal name: Federative Republic of Brazil
Capital: Brasília
Location: Americas · South America
Population snapshot: 209,469,333
Currency: Brazilian Real (BRL, R$)
Languages: English (en), Spanish (es), French (fr), Portuguese (pt-BR)
Anthem title: Hino Nacional Brasileiro · Brazilian National Anthem
Motto: Ordem e Progresso · Order and Progress
Highest point: Pico da Neblina (2,994 m)
Dominant climate class: Aw · Tropical, savannah
Source-listed rivers: Amazon, Río de la Plata/Paraná, Tocantins
Source-listed lakes: Lagoa dos Patos, Lagoa Mirim
```

`Atlas` opens a bundled, read-only SQLite database. Results are immutable,
typed models rather than loosely structured dictionaries, and loaded records
remain usable after the atlas is closed.

## Open the terrain

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    atlas.map("Iceland").show()
```

The one-line call opens a local, rotatable 3D map in the default browser with
elevation, Köppen-Geiger climate coloring, rivers, the country outline, and the
primary capital. The viewer and data remain offline after installation. Use
`atlas.map("Iceland").write_html("iceland-map.html")` to create a standalone
document for a lesson or presentation.

[Compare the map editions and learn the API](https://jcari-dev.github.io/pyworldatlas-documentation/maps.html).

## What you can explore

| Area | Included capabilities |
|---|---|
| Country profiles | Codes, names, capitals, population, currencies, languages, timezones, postal formats, anthem titles, reviewed mottos, and demonyms |
| Names and writing systems | English identities, selected local-language names, scripts, reviewed official forms, and source-provided romanization |
| Physical geography | Land and water area, coastline, elevation extremes, rivers, lakes, and climate summaries |
| Interactive maps | Optional offline 3D elevation and climate surfaces for all 248 profiles, with rivers and capitals |
| Places and measurement | 6,265 cities and capitals with search, nearby-place discovery, readable coordinates, distance, compass direction, bearing, and midpoint calculations |
| Land connections | Reviewed neighbors, shared neighbors, shortest border paths, crossings, and connected components |
| Learning tools | Readable profiles, stable samples, flashcards, deterministic multiple-choice questions, rankings, discovery cards, and Unicode-preserving JSON |

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

    print(tokyo.coordinates.format())
    print(tokyo.coordinates.dms())
    print(f"{atlas.distance_between(tokyo, paris):,.0f} km")
    print(tokyo.coordinates.compass_direction_to(paris.coordinates))

    nearby = atlas.nearest_cities(tokyo, within_country="JP", limit=3)
    print([result.city.name for result in nearby])

    route = atlas.border_path("Portugal", "China")
    print(" → ".join(route.names))
```

Build a repeatable lesson:

```python
with Atlas() as atlas:
    questions = atlas.quiz(topic="local_names", count=5, seed=42)

    for question in questions:
        print(question.prompt)
        for number, choice in enumerate(question.choices, 1):
            print(f"  {number}. {choice}")
        print("Answer:", question.answer_number)
```

Distances are great-circle surface measurements, not road or flight routes.
Border paths use the reviewed land-border graph and do not infer maritime or
boundary geometry.

## Built for learning

- **Offline:** lessons and programs do not depend on an external service.
- **Repeatable:** seeded samples, flashcards, and quizzes produce stable results.
- **Source-aware:** provenance and coverage limits are documented.
- **Beginner-friendly:** common tasks use small Python objects and methods.
- **Honest about missing data:** unavailable values remain `None` or empty tuples.

The project provides factual geography and transparent calculations, not
political commentary or opinion. Read the
[educational and neutrality policy](https://github.com/jcari-dev/pyworldatlas/blob/main/docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md) for
the formal publication standard.

## Coverage at a glance

Library `0.9.0` includes dataset `2026.07.22.7` and schema `7`.

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
| Overview and Standard map coverage | 248 / 248 each |

See the generated [project status](https://jcari-dev.github.io/pyworldatlas-documentation/_generated/project_status.html)
for complete coverage and [data quality](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html)
for interpretation limits.

## Data and trust

Field families use defined source roles rather than one unreviewed compilation.
The builder retains source snapshots, checksums, review decisions, and exact
coverage gates. Sources include United Nations M49, GeoNames, Unicode CLDR,
UNGEGN, Natural Earth, the CIA World Factbook, Wikidata, IANA registries, and
the Beck et al. Köppen-Geiger dataset, and NOAA NCEI ETOPO 2022.

- [Data sources and freshness](https://jcari-dev.github.io/pyworldatlas-documentation/data_sources.html)
- [Data quality and limitations](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html)
- [Educational purpose and editorial policy](https://github.com/jcari-dev/pyworldatlas/blob/main/docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md)
- [Third-party notices](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md)

## Documentation and community

- [Run Python in the browser](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html)
- [Try the classroom-friendly learning lab](https://jcari-dev.github.io/pyworldatlas-documentation/learning.html)
- [Browse complete recipes](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html)
- [Read the country-profile guide](https://jcari-dev.github.io/pyworldatlas-documentation/country_profile.html)
- [Explore physical geography](https://jcari-dev.github.io/pyworldatlas-documentation/physical_geography.html)
- [Open interactive 3D maps](https://jcari-dev.github.io/pyworldatlas-documentation/maps.html)
- [Review the API](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)
- [See the roadmap](https://github.com/jcari-dev/pyworldatlas/blob/main/ROADMAP.md)

Questions, factual corrections, documentation improvements, and focused code
contributions are welcome. Start with
[CONTRIBUTING.md](https://github.com/jcari-dev/pyworldatlas/blob/main/CONTRIBUTING.md),
follow the
[code of conduct](https://github.com/jcari-dev/pyworldatlas/blob/main/CODE_OF_CONDUCT.md),
and report security concerns through
[SECURITY.md](https://github.com/jcari-dev/pyworldatlas/blob/main/SECURITY.md).

## Development

```console
python maintain.py bootstrap
python maintain.py check
```

`maintain.py check` runs tests, builds the core and optional-map distributions,
installs the wheels in isolation, renders an offline map, executes examples,
builds strict documentation and doctests, and audits the release contents.

## License

PyWorldAtlas code is available under the
[MIT License](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE). Bundled data
retains its original terms and attribution; see
[THIRD_PARTY_NOTICES.md](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md).
