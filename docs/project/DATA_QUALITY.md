# Data quality policy

## Educational and editorial quality

PyWorldAtlas provides offline factual geography for education and reference.
It does not provide political commentary or opinion. Every field must have a
clear learning purpose, a defined source role, and documented limitations.
Missing values are not replaced with unsupported assumptions.

The current dataset intentionally excludes current affairs, political opinion,
identity-based generalizations, comparisons of people or cultures, and
speculative narrative. New field families must satisfy the review in
`EDUCATIONAL_AND_NEUTRALITY_POLICY.md` before collection begins.

The pipeline validates required identifiers, every stored coordinate, explicit
capital coverage, SQLite integrity, foreign keys, and deterministic ordering.
Raw snapshots are immutable and checksummed. Familiar common-name overrides
retain the official UN M49 value and are reviewed in
`pipeline/config/overrides.json`.

The 0.9.4 package includes 248 countries and areas from the captured UN M49
scope, 241 primary-capital records, and 6,265 populated-place records. The
place table contains records at or above 100,000 population plus retained
capitals. Seven areas expose a missing capital as `None`. GeoNames-only
identities outside the UN M49 snapshot are excluded; this is a source-scope
decision.

The current dataset requires exactly one local identity for each of the 248
country and area records. It spans 80 languages and 21 scripts. Validation
requires unique country coverage, language and ISO 15924 script metadata, an
evidence kind, language-selection status, captured-source identifier, and exact
source locator. All names use Unicode NFC.

Ten selected records currently contain reviewed UNGEGN national short and
formal names. The other 238 are Unicode CLDR display names whose formal and
romanized fields remain `None`. Four remote or uninhabited areas have explicit
non-official administrative or non-applicable language selections rather than
a fabricated official-language claim.

The separate English formal-name layer covers 240 profiles. It contains 195
distinct long forms and 45 cases where the source uses the same text for the
short and formal identity. The builder validates the pinned Factbook extraction
and all eight reviewed exceptions against their exact UN page or Wikidata
statement locator. AX, BQ, GF, GP, MQ, RE, UM, and YT remain explicit `None`
values because they are outside the captured source intersection.

Rich-profile validation requires non-negative population snapshots, structured
calling-code and language-code collections, valid currency identifiers when
present, and documented missing values. Coordinate validation rejects latitude
outside -90 through 90 and longitude outside -180 through 180. Distance,
bearing, and midpoint tests use known city pairs and never present spherical
distance as a road or routing result.

Current profile coverage is 248 population snapshots, 247 currency records,
245 language-code collections, 243 calling-code collections, 248 top-level
domains, and 242 profiles with at least one observed timezone. These are source
snapshots, not live or exhaustive registries.

Version 0.6 adds 234 anthem-title profiles, 32 reviewed source-listed mottos,
227 English demonym profiles, 417 country-level timezone records across 246
profiles, 176 postal-code formats, and 722 country-language metadata records
across 245 profiles. The builder pins each source snapshot and requires an
explicit decision for every captured motto statement. Language associations
are source metadata, not legal-language determinations. Motto records do not
infer official, traditional, constitutional, or statutory status.

Anthem records contain titles only. Lyrics, audio, contributor credits,
adoption histories, and narrative text are excluded. Missing motto or anthem
records describe the current reviewed source coverage; they do not claim that a
country has no motto or anthem.

Version 0.7 adds total-area coverage for all 248 profiles; 238 land-area and
coastline profiles; 233 numeric water-area profiles; 240 highest points, lowest
points, and short climate summaries; 166 mean-elevation profiles; 188
source-listed river records across 80 profiles; 187 source-listed lake records
across 69 profiles; and Köppen-Geiger classes for 241 profiles. The builder pins
both source and derived checksums and validates the exact coverage and gap sets.

River and lake collections are source-listed major features, not exhaustive
inventories. Empty collections do not assert absence. A shared river's length
or lake's area describes the complete source feature rather than its portion
inside one country. Highest points are not relabelled as a separate major-
mountain inventory.

Köppen-Geiger shares are latitude-area-weighted estimates from the 0.1-degree
1991–2020 raster and generalized map-unit polygons. Classes below 0.1% of a
profile's represented cells are omitted. These values support broad education,
not site-level climate determination or forecasting.

The land-border build compares GeoNames neighbor records with shared segments
from Natural Earth 1:50m map-unit polygons. It requires explicit decisions for
every source difference, canonicalizes each accepted pair, rejects self-edges
and unknown endpoints, and tests runtime symmetry. The current graph contains
319 undirected relationships: 315 cross-source agreements and four reviewed
inclusions. Eighty-five entities have no accepted land border.

The graph represents topological adjacency only. It does not supply border
geometry, length, maritime boundaries, or road routes. Geometry, GeoJSON,
bounding boxes, centroids, and point-in-country lookup are deferred beyond
0.7. Generalized source
geometry, small territories, enclaves, and disputed areas are handled according
to [BOUNDARIES_AND_DISPUTES.md](BOUNDARIES_AND_DISPUTES.md).

The optional 0.9 map editions contain one integrity-hashed record for every
profile. Overview uses 20 arc-minute and Standard uses 5 arc-minute ETOPO
sampling. Automated gates verify exact 248-profile coverage, readable payloads,
grid dimensions, non-empty display masks, source metadata, and clean-wheel
installation. These are generalized educational surfaces. Tiny islands,
coastlines, rivers, and climate transitions may be simplified or displaced by
the source resolution; the maps are not suitable for navigation or local
decision-making.

These boundaries are publication-safety rules as well as data limitations.
Factual corrections are welcomed when they identify the affected field, source,
date, and reason the current value is inaccurate within the documented scope.
