# Changelog

## 0.3.0 — 2026-07-21

- Added 319 reviewed, undirected land-border relationships across the existing
  248-country-and-area scope.
- Added neighbor lookup, shared-border tests, shared neighbors, deterministic
  shortest border paths, minimum crossing counts, land-connected components,
  and borderless-entity discovery.
- Added the immutable, serializable `BorderPathResult` model.
- Added a strict source review gate: 315 GeoNames/Natural Earth agreements plus
  explicit decisions for all six differences between the pinned snapshots.
- Added Natural Earth source captures, checksums, public-domain terms, graph
  validation, executable examples, and complete border documentation.
- Upgraded the generated dataset to schema 3 and consolidated validation into
  focused examples and automated tests.

## 0.2.1 — 2026-07-21

- First production candidate for the complete 0.2 country-profile, coordinate,
  and discovery feature set.
- Supersedes the unpublished 0.2.0 candidate without changing its public API or
  bundled dataset.

## 0.2.0 — Unpublished candidate

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
