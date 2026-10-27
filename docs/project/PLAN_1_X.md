# 1.x plan

This document records the planned scope of the 1.x series. Planned work is not
part of the public API until it is implemented, tested, documented, and
published. Every item below remains subject to the data-admission rules and to
the review in `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.

## Versioning

The 1.x series uses few, themed minor releases:

- A minor release (1.1, 1.2, ...) ships one large, coherent theme.
- Patch releases (1.1.1, 1.1.2, ...) ship fixes and small additions inside the
  current theme.
- A major release is reserved for an unavoidable breaking change.

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

The 1.x series ships **one** PyPI package. Additional data is installed as data
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

This changes how maps install, so it lands before the 1.0 API freeze.

## 1.0: Stable and instant

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

## 1.1: Every place on Earth

- **Places pack:** populated places of 5,000 or more inhabitants and
  first-level subdivisions with their codes (GeoNames).
- **Landmarks pack:** airports (OurAirports), World Heritage sites, mountains,
  volcanoes, islands, deserts, seas, and ranges from open sources.
- **Travel basics in core:** plug types, mains voltage and frequency, and
  driving side.
- One lookup across countries, places, subdivisions, and landmarks.
- Proximity search over all installed places.
- Explorable 3D maps: every installed place type (cities, subdivisions,
  airports, landmarks) as layers that can be searched, filtered, and clicked
  for their facts on the map.

## 1.2: The world in numbers

Requires an "official statistics" section in the editorial policy first.

- **Statistics pack:** selected World Bank indicators from 1960 and UN
  population estimates from 1950, with UN projections labeled as projections.
- Every value carries unit, reference year, and source.
- Time series, side-by-side fact listing without judgement, and one-line
  charts.
- Map coloring by any indicator.

## 1.3: The encyclopedia

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
