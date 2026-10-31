# PyWorldAtlas: offline world geography for Python

> Offline world atlas for Python: 248 countries, 11 million places, statistics since 1960, and 3D maps, with zero dependencies. Built for low-cost computers with 512 MB of memory, such as a Raspberry Pi Zero 2 W; the core installs in under a minute on slow 3G.

[![PyPI](https://img.shields.io/pypi/v/pyworldatlas.svg?label=PyPI&color=287aa3)](https://pypi.org/project/pyworldatlas/)
[![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776ab)](https://www.python.org/)
[![CI](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml/badge.svg)](https://github.com/jcari-dev/pyworldatlas/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-317f78)](https://jcari-dev.github.io/pyworldatlas-documentation/)
[![Code: MIT](https://img.shields.io/badge/code-MIT-607087)](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE) [![Data: CC BY 4.0 and others](https://img.shields.io/badge/data-CC%20BY%204.0%20%2B%20others-607087)](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md)

**248 countries · 200,000 places built in · 11 million with packs · statistics since 1960 · airports and World Heritage sites · 248 3D maps · 0 dependencies**

[![Animated PyWorldAtlas 3D map of Iceland with towns, mountains, water, and landmarks](https://raw.githubusercontent.com/jcari-dev/pyworldatlas/main/docs/source/_static/iceland-rotation.gif)](https://jcari-dev.github.io/pyworldatlas-documentation/maps.html)

## Try it in 10 seconds

No install: open the [browser playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html), type a
country or place, take a quiz, or run a ready-made program.

Or install it (Python 3.10 to 3.14, nothing else needed):

```console
python -m pip install pyworldatlas
pyworldatlas --version
pyworldatlas find Everest
```

## A taste

```python
from datetime import date
from pyworldatlas import Atlas

with Atlas() as atlas:
    print(atlas.country("Japan").travel.summary)      # Plugs A, B · 100 V, 50/60 Hz · drives on the left
    print(atlas.search_places("Everest", limit=1)[0])  # Mount Everest, mountain (NP)
    print(atlas.sun("Oslo", date(2026, 12, 21)).daylight)  # 5 h 54 min
    print(atlas.antipode("Madrid").nearest[0].place)  # Ossa, mountain (NZ): dig through the Earth
    atlas.map("Iceland").show(auto_rotate=True)        # 3D map (pyworldatlas get maps)
```

## What's inside

| | |
|---|---|
| **Countries** | 248 profiles: names in local scripts, capitals, languages, currencies, travel basics, climate, highest points, rivers, and borders |
| **Places** | 200,000 towns, mountains, lakes, and landmarks built in; 11 million with packs; search by local or English name and list what is nearby |
| **Learning** | Flashcards and quizzes that repeat for a whole class, place quizzes, sun and seasons, and antipodes |
| **Optional packs** | `pyworldatlas get maps` (3D maps), `statistics` (World Bank numbers since 1960), `landmarks` (airports and World Heritage sites), `places-explorer` and `places-world` |

Everything works offline after installation, needs no API key, and is built
for low-cost computers and slow connections. Every value is traced to a named
source; missing data stays missing.

## Start here

- 🧒 **Students:** the [playground](https://jcari-dev.github.io/pyworldatlas-documentation/playground.html), [quests](https://jcari-dev.github.io/pyworldatlas-documentation/quests.html), and [learning activities](https://jcari-dev.github.io/pyworldatlas-documentation/learning.html)
- 🍎 **Teachers and classrooms:** [teaching with PyWorldAtlas](https://jcari-dev.github.io/pyworldatlas-documentation/teaching.html), with a 15-minute lesson and printable quizzes
- 💻 **Developers:** the [quickstart](https://jcari-dev.github.io/pyworldatlas-documentation/quickstart.html), [cheat sheet](https://jcari-dev.github.io/pyworldatlas-documentation/cheatsheet.html), [example programs](https://jcari-dev.github.io/pyworldatlas-documentation/recipes.html), and [API reference](https://jcari-dev.github.io/pyworldatlas-documentation/api.html)

## Trust and neutrality

PyWorldAtlas presents factual geography from public sources, with no political
commentary. Country names and codes follow published international standards,
and the project takes no position on disputes. See the
[educational and neutrality policy](https://github.com/jcari-dev/pyworldatlas/blob/main/docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md),
[data sources](https://jcari-dev.github.io/pyworldatlas-documentation/data_sources.html), and [data quality](https://jcari-dev.github.io/pyworldatlas-documentation/data_quality.html).

## Contributing

Questions, corrections, and focused contributions are welcome: see
[CONTRIBUTING.md](https://github.com/jcari-dev/pyworldatlas/blob/main/CONTRIBUTING.md), the
[code of conduct](https://github.com/jcari-dev/pyworldatlas/blob/main/CODE_OF_CONDUCT.md), and [SECURITY.md](https://github.com/jcari-dev/pyworldatlas/blob/main/SECURITY.md).
`python maintain.py check` runs the full test, build, and documentation gate.

## License

PyWorldAtlas code is available under the
[MIT License](https://github.com/jcari-dev/pyworldatlas/blob/main/LICENSE). The data keeps
its own terms, and every source is credited:

- Places, cities, and country metadata: [GeoNames](https://www.geonames.org/), CC BY 4.0
- Local names, currencies, and languages: [Unicode CLDR](https://cldr.unicode.org/), Unicode License v3
- Statistics pack: [World Bank World Development Indicators](https://datacatalog.worldbank.org/), CC BY 4.0
- Also: CIA World Factbook and Natural Earth (public domain), Wikidata, IANA,
  NOAA ETOPO 2022, and Beck et al. Köppen-Geiger maps (CC0), OurAirports
  (public domain), and United Nations M49 and naming documents

Full credits, the changes made, and license texts are in
[THIRD_PARTY_NOTICES.md](https://github.com/jcari-dev/pyworldatlas/blob/main/THIRD_PARTY_NOTICES.md)
and `licenses/`. The package metadata license is
`MIT AND CC-BY-4.0 AND Unicode-3.0 AND CC0-1.0`.
