# Data quality

The pipeline validates required identifiers, coordinates, capital coverage,
SQLite integrity, foreign keys, and deterministic ordering. Raw snapshots are
immutable and checksummed. Familiar common-name overrides retain the official
UN M49 value and are reviewed in `pipeline/config/overrides.json`. Release 0.1.0
is intentionally a twelve-country dataset, not full-world coverage.

