# Data quality

The pipeline validates required identifiers, every stored coordinate, explicit
capital coverage, SQLite integrity, foreign keys, and deterministic ordering.
Raw snapshots are immutable and checksummed. Familiar common-name overrides
retain the official UN M49 value and are reviewed in
`pipeline/config/overrides.json`.

Release 0.1.0 includes 248 countries and areas from the captured UN M49 scope,
241 primary-capital records, and 6,265 major-city records. Seven areas expose a
missing capital as `None`. GeoNames-only identities outside the UN M49 snapshot
are excluded rather than inferred; this source-priority rule is not a statement
about sovereignty.
