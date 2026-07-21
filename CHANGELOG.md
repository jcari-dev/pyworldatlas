# Changelog

## 0.2.0 — Unreleased

- Added richer country profiles with population snapshots, currencies, language
  codes, calling codes, top-level domains, observed timezones, and direct
  primary-capital coordinates.
- Added exact city lookup, validated latitude/longitude objects, great-circle
  distance in three units, initial bearings, spherical midpoints, and named-place
  distance helpers.
- Added sourced official local short and formal names for Brazil and
  Switzerland.
- Added language/script metadata, explicit romanization fields, per-record
  provenance, serialization, and no-fallback lookup helpers.
- Added `flag_emoji`, calculated population density, compact country
  references, and serializable discovery cards.
- Added deterministic country sampling and structured flashcards for capitals,
  flags, codes, currencies, communications, regions, local names, and snapshot
  population/area facts.
- Upgraded the generated dataset to schema 2 while preserving 0.1.0 lookup,
  country, capital, city, and collection behavior.

## 0.1.0 — 2026-07-20

- Rebuilt the project from scratch around a standard-library runtime and one generated SQLite database.
- Added lookup, aliases, standard identifiers, and UN regions for 248 countries and areas.
- Added 241 primary-capital records and 6,265 major-city records from GeoNames.
- Added a separate deterministic source-ingestion project, offline rebuild, tests, wheel demo, and canonical documentation source.
