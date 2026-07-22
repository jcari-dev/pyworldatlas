# Roadmap

PyWorldAtlas advances through installable, documented releases with explicit
data boundaries. Versions 0.1 through 0.5 established the generated offline
database, typed profiles, coordinates and distances, reviewed land-border
tools, complete selected local identities, English formal names, and the
educational/editorial policy.

## 0.6.0 — Country reference and discovery

The published 0.6 release adds:

- 234 national-anthem title profiles, without lyrics, audio, credits, or dates.
- 32 explicitly reviewed source-listed national mottos.
- 227 English demonym profiles.
- CLDR currency names, symbols, and minor-unit metadata.
- Language names and likely scripts for the captured country-language records.
- 417 country-level timezone records across 246 profiles.
- 176 postal-code formats.
- Exact currency, language, script, and timezone filters.
- Typed country rankings and nearest-capital results.
- A documentation-first example gallery and focused reference guides.

## 0.7.0 — Physical geography

The 0.7 release candidate adds:

- Sourced total, land, and water area plus calculated water percentage.
- Coastline, mean elevation, and named highest and lowest points.
- Source-listed major rivers and lakes with clear shared-feature semantics.
- Plain-language climate summaries and represented 1991–2020 Köppen-Geiger
  classes.
- Physical filters, feature search, rankings, discovery-card fields, and
  deterministic flashcards.
- Pinned inputs, deterministic extraction, exact coverage gates, and a focused
  physical-geography documentation guide.

A separate “major mountains” inventory is not claimed. The available source
reliably identifies highest points but does not provide a consistent global
major-mountain threshold.

## Deferred beyond 0.7

Country boundary geometry, GeoJSON export, bounding boxes, centroids, and
point-in-country lookup are explicitly deferred. Reference dates and anthem
contributors/adoption histories also remain outside the current contract.

`ROADMAP_STATUS.md` contains generated implementation evidence. Release gates
and publication instructions are maintained in the version-specific status
documents and `RELEASING.md`.
