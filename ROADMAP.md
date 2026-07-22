# Roadmap

PyWorldAtlas advances through installable, documented releases with explicit
data boundaries. Versions 0.1 through 0.5 established the generated offline
database, typed profiles, coordinates and distances, reviewed land-border
tools, complete selected local identities, English formal names, and the
educational/editorial policy.

## 0.6.0 — Country reference and discovery

The 0.6 release candidate adds:

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

The planned 0.7 scope is land and water area, coastline length, highest and
lowest points, elevation, named major rivers/lakes/mountains, reviewed Köppen
climate classifications, and rankings derived from those physical fields.
Every field family needs a pinned, legally usable source and an honest coverage
gate before it enters the package.

## Deferred beyond 0.7

Country boundary geometry, GeoJSON export, bounding boxes, centroids, and
point-in-country lookup are explicitly deferred. Reference dates and anthem
contributors/adoption histories also remain outside the current contract.

`ROADMAP_STATUS.md` contains generated implementation evidence. Release gates
and publication instructions are maintained in the version-specific status
documents and `RELEASING.md`.
