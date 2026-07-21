# Data quality

The pipeline validates required identifiers, every stored coordinate, explicit
capital coverage, SQLite integrity, foreign keys, and deterministic ordering.
Raw snapshots are immutable and checksummed. Familiar common-name overrides
retain the official UN M49 value and are reviewed in
`pipeline/config/overrides.json`.

The 0.2.0 checkout includes 248 countries and areas from the captured UN M49
scope, 241 primary-capital records, and 6,265 populated-place records. The
place table contains records at or above 100,000 population plus retained
capitals. Seven areas expose a missing capital as `None`. GeoNames-only
identities outside the UN M49 snapshot are excluded; this source-priority rule
is not a statement about sovereignty.

Version 0.2.0 includes five official local-name records for Brazil and
Switzerland. Validation requires a unique country/language pair, language
and ISO 15924 script metadata, short and formal forms, an official-language
flag, a captured-source identifier, and an exact entry/page locator. Countries
outside the pilot return an empty tuple rather than an inferred value.

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
