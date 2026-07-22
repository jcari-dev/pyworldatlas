# Data quality

The pipeline validates required identifiers, every stored coordinate, explicit
capital coverage, SQLite integrity, foreign keys, and deterministic ordering.
Raw snapshots are immutable and checksummed. Familiar common-name overrides
retain the official UN M49 value and are reviewed in
`pipeline/config/overrides.json`.

The 0.4.0 development checkout includes 248 countries and areas from the captured UN M49
scope, 241 primary-capital records, and 6,265 populated-place records. The
place table contains records at or above 100,000 population plus retained
capitals. Seven areas expose a missing capital as `None`. GeoNames-only
identities outside the UN M49 snapshot are excluded; this source-priority rule
is not a statement about sovereignty.

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

The land-border build compares GeoNames neighbor records with shared segments
from Natural Earth 1:50m map-unit polygons. It requires explicit decisions for
every source difference, canonicalizes each accepted pair, rejects self-edges
and unknown endpoints, and tests runtime symmetry. The current graph contains
319 undirected relationships: 315 cross-source agreements and four reviewed
inclusions. Eighty-five entities have no accepted land border.

The graph represents topological adjacency only. It does not supply border
geometry, length, maritime boundaries, or road routes. Generalized source
geometry, small territories, enclaves, and disputed areas are handled according
to [BOUNDARIES_AND_DISPUTES.md](BOUNDARIES_AND_DISPUTES.md).
