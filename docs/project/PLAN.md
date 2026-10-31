# Release plan

This document records the planned scope of the next releases. Planned work is not
part of the public API until it is implemented, tested, documented, and
published. Every item below remains subject to the data-admission rules and to
the review in `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.

## Versioning

PyWorldAtlas grows through few, themed releases on the way to 1.0:

- A release (0.11, 0.12, ...) ships one large, coherent theme.
- Patch releases (0.11.1, 0.11.2, ...) ship fixes and small additions inside the
  current theme.
- Version 1.0 comes once the public API has proven stable in real use. From
  then on, a major release is reserved for an unavoidable breaking change.

## Who PyWorldAtlas is for

PyWorldAtlas is for every audience and every age: learners, classrooms,
teachers, hobbyists, and developers. It is an educational project that makes
reliable world information easy to reach and invites people to learn
programming by exploring it. Two requirements follow from that purpose and
apply to every release:

- **Fully accessible.** Documentation, the map page, and command-line output
  meet WCAG 2.2 AA: complete keyboard use, text alternatives for visual
  content (including the 3D map), sufficient contrast, respect for reduced
  motion, and plain, friendly language.
- **Extremely fast.** Every feature stays responsive on modest and older
  hardware, within the performance budgets below.

## Principles every release must keep

1. **Offline at runtime.** Queries never use the network.
2. **Every fact is sourced and dated.** Values keep a source record and, where
   the value changes over time, an explicit reference year.
3. **Neutral and factual.** No rankings by opinion, no editorial labels, no
   current affairs.
4. **Missing stays missing.** Gaps are `None`, never inferred.
5. **Reproducible.** Every source snapshot is pinned and checksummed.
6. **Zero runtime dependencies.** The package uses only the Python standard
   library, maps included. Large data ships as optional data packs.
7. **Fast on modest hardware.** Performance budgets are enforced in CI.
8. **Accessible to everyone.** New pages, controls, and messages meet
   WCAG 2.2 AA and are written in plain language.
9. **Licenses first.** A source's license is verified and shipped before its
   data is collected.

## Data-admission rules

A dataset is admitted only when all of the following hold:

- it is publicly and freely available from the original publisher;
- it comes from a standards body, an international statistical publisher, an
  established open geographic dataset, or individually reviewed Wikidata
  statements;
- its license permits redistribution and is shipped with the data;
- each value can be traced to its source record;
- it states facts without judgement.

The following are excluded regardless of availability: religious or ethnic
breakdowns; crime, corruption, freedom, happiness, or similar composite
indices; political office-holders, elections, conflicts, and current events;
generalizations about people; disputed-territory claims beyond the existing
boundary policy; and free narrative text from wikis or blogs. When a dataset is
in doubt, it is left out.

## Installation model

PyWorldAtlas ships **one** PyPI package. Additional data is installed as data
packs rather than as separate PyPI distributions.

```console
pip install pyworldatlas            # core, works immediately
pyworldatlas get places             # download a data pack
pyworldatlas get maps --lite        # smaller map edition for modest hardware
pyworldatlas get everything
pyworldatlas add ./places.pack      # install a pack from a local file
pyworldatlas packs                  # list installed and available packs
```

```python
Atlas(data_dir="D:/world-packs")    # or the PYWORLDATLAS_DATA variable
```

- Packs download only when the user runs `get`; normal use stays offline.
- Each library release pins the SHA-256 checksum of every compatible pack, so
  modified or mismatched files are rejected.
- Each pack carries its own source records and license files.
- Three named levels: **lite** (core only), **standard** (core, places, lite
  maps), and **full** (everything).
- The map viewer lives in the core package with no plotting dependency:
  Python builds the scene data with the standard library, and the map packs
  ship the browser renderer as a static asset. The `maps` and
  `maps-overview` extras are kept, empty, so older install commands still work.
- Packs are attached to GitHub releases, replacing the separate
  `pyworldatlas-mapview` and `pyworldatlas-mapdata-*` distributions. (Done.)

This changed how maps install and shipped in 0.10.

## 0.10: Stable and instant (released)

No new data families; the existing data becomes dependable and fast.

- Performance: every public call under 10 ms on the reference benchmark.
- Correct shared caching across `Atlas` instances.
- Typed package (`py.typed`) with a type check in CI.
- Measured test coverage, with a lint step in CI.
- CI on Linux, Windows, and macOS.
- Frozen public API with a snapshot test.
- Data-pack installation model (above).
- Maps: city markers, elevation-extreme markers, lakes, neighbor scenes,
  click-for-facts, and a lite rendering mode.
- Rich notebook display for country profiles.
- Accessibility audit and fixes for the documentation site and the map page:
  a text summary of each map (terrain range, climate classes, rivers, capital)
  for screen readers, keyboard-only use, contrast, and focus order.
- Performance budgets checked automatically, including import time and the
  first full collection load.

## 0.11: Every place on Earth

Promise: a complete school atlas in every install, under a minute to download
on a slow 3G connection, and every place on Earth under 2 minutes on a slow
5 Mbps line.

- **Done: school atlas in core.** 207,664 places ranked by educational value
  (2 MB): every country, region, town of 5,000 or more, and widely known
  natural feature and landmark, from GeoNames. Search by local or English name,
  best known first, and exact nearest-place search.
- **Done: place packs.** `places-explorer` (every town over 1,000 and every
  named natural feature) and `places-world` (everything else worth knowing),
  11 million places in all.
- **Done: landmarks pack.** Airports with scheduled flights (OurAirports) and
  UNESCO World Heritage sites (Wikidata), with a reviewed country table.
- **Travel basics in core:** plug types, mains voltage and frequency, and
  driving side.
- **Done: one lookup** across countries, places, regions, and landmarks
  (`Atlas.lookup`, `pyworldatlas find`).
- **Done: proximity search** over all installed places (`Atlas.places_near`).
- **Done: places on 3D maps.** Towns, mountains and islands, lakes and seas,
  and landmarks as layers that can be shown, hidden, and hovered for their
  facts (`Atlas.map(..., places=8)`, `Atlas.places_in`).
- **Done: search on the map** (Find a place box on the map page).
- Explorable 3D maps, next: airport and World Heritage layers.

## 0.12: The world in numbers

- **Done: official statistics policy.** The "Official statistics" section of
  the editorial policy sets the publishers, labelling, scope, presentation,
  and missing-value rules below.
- **First indicator shortlist** (each needs its license and definition checked
  before collection): population, population density, urban population share,
  life expectancy at birth, births and deaths per 1,000 people, median age,
  forest area share, agricultural land share, access to electricity, access
  to safe drinking water, internet users share, and primary school
  enrollment.
- **License notes (checked 2026-10-27).** The World Bank data catalog lists
  World Development Indicators under CC BY 4.0. WDI collects some series from
  partner agencies, so each indicator's own license field must also read
  CC BY 4.0 before it is admitted. The UN World Population Prospects terms
  still need to be confirmed from the publisher before any WPP value is used.

- **Done: statistics pack.** Eleven World Bank indicators from 1960 (CC BY
  4.0), with time series, sorting, one-line charts, and sentences.
- Every value carries unit, reference year, and source.
- Time series, side-by-side fact listing without judgement, and one-line
  charts.
- **Done: map coloring by any indicator** (`Atlas.world_map`,
  `pyworldatlas world-map`).

## 0.13: Friendly by default (released)

- **Done: one naming style.** Distance searches end in `_near`, `rank()`
  ranks statistics too, `quiz()` takes every topic, and older names keep
  working until 1.0.
- **Done: results that read well,** "did you mean" suggestions,
  `atlas.help()`, and `pyworldatlas tour`.
- **Done: world maps of statistics** (`Atlas.world_map`).
- **Done: friendlier docs.** A shorter welcome page, a cheat sheet, quests, a
  glossary, "Try it" links, and dark mode that passes WCAG 2.2 AA.

## 0.14: The encyclopedia

- Generated reference entries for every country, place, and landmark, built
  only from sourced structured data.
- Offline static-site export of the full atlas, maps, and charts.
- Command-line entries and proximity queries.
- Learning tools extended to the new data.

## Performance budgets

| Measure | Budget |
|---|---|
| `import pyworldatlas` | under 50 ms |
| Any single lookup | under 5 ms |
| Proximity search over 50,000+ places | under 10 ms |
| Core memory | under 50 MB |
