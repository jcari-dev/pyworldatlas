Changelog
=========

0.2.0 — Unreleased
------------------

- Added rich profile fields for population snapshots, currency, language codes,
  calling codes, top-level domains, observed timezones, and capital coordinates.
- Added exact city lookup, coordinate validation, great-circle distance, initial
  bearing, spherical midpoint, and named-place distance helpers.
- Added five sourced official local-name records across Brazil and Switzerland.
- Added language and script metadata, formal names, explicit romanization
  fields, provenance, and no-fallback convenience methods.
- Upgraded the generated dataset to schema 2 while retaining the 0.1.0 country,
  capital, city, lookup, and collection behaviors.

0.1.0 — 2026-07-20
------------------

- Rebuilt the project from scratch around a standard-library runtime and one
  generated SQLite database.
- Added lookup, aliases, standard identifiers, and UN regions for 248 countries
  and areas.
- Added 241 primary-capital records and 6,265 major-city records from GeoNames,
  with explicit missing values for areas without usable capitals.
- Added a separate deterministic source-ingestion project with raw manifests,
  normalized records, provenance, validation, and reproducibility checks.
- Added clean-wheel installation tests, executable examples, and documentation
  generated from the installed wheel.
- Added a VS Code playground with all-record audits.
- Added Sphinx documentation with executable doctests.

Legacy releases
---------------

Versions 0.0.1 through 0.0.12 belong to the legacy prototype and remain on PyPI.
Version 0.1.0 begins the rebuilt source-aware architecture in the repository.
