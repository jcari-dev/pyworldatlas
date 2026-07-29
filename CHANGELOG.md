# Changelog

## 0.9.2

- Added terrain-height controls and selectable capital and river labels to the
  interactive 3D map viewer.
- Strengthened capital markers and labels for clear presentation at varied
  camera angles.
- Corrected the downstream Þjórsá label in the Standard Iceland map using a
  reviewed national source.

## 0.9.1

- Published the optional map viewer and both global map editions through
  isolated Trusted Publishing jobs.
- Kept the 0.9 map API and dataset unchanged while correcting the coordinated
  package release configuration.

## 0.9.0

- Added optional offline 3D country maps through `Atlas.map()` and the
  browser-opening `CountryMap.show()` interface.
- Added Overview and Standard global map editions covering all 248 existing
  profiles with 20 and 5 arc-minute elevation sampling, respectively.
- Added elevation and Köppen-Geiger climate surface modes, generalized country
  outlines, source-provided river centerlines, and primary-capital markers.
- Added standalone offline HTML export and direct access to the underlying
  Plotly figure for notebooks and customization.
- Kept the core wheel dependency-free by publishing the viewer and each map
  edition as separately installable companion distributions.
- Added reproducible map-pack generation, complete coverage and integrity
  tests, clean multi-wheel installation, and map-aware release automation.
- Documented installation choices, exact wheel sizes, sources, resolution,
  generalization limits, and the non-navigational educational scope.
- Added a real Standard-edition Iceland render to the GitHub/PyPI README and
  documentation front page, linked directly to the interactive map guide.

## 0.8.1

- Added concise browser-tab titles, a globe favicon, canonical page metadata,
  social preview metadata, a generated sitemap, and crawler guidance for the
  public documentation site.
- Refined the shared GitHub and PyPI README introduction and made repository
  links portable across both renderers.

## 0.8.0

- Added `Country.summary()` for readable multilingual country introductions
  built from existing sourced profile fields.
- Added deterministic multiple-choice questions through `Atlas.quiz()` and the
  immutable, serializable `QuizQuestion` model.
- Added `Atlas.learning_topics()` so applications and lessons can discover the
  topics shared by flashcards and quizzes.
- Added partial `Atlas.search_cities()` lookup and `Atlas.nearest_cities()`
  proximity discovery with typed `CityDistance` results.
- Added decimal-degree formatting, degrees/minutes/seconds formatting,
  hemisphere labels, and compass directions to `Coordinate`.
- Added compact human-readable city labels.
- Expanded beginner examples, classroom recipes, the browser playground, API
  documentation, and docstrings around the education and usability workflows.
- Reorganized the documentation as a coherent learning path and retained the
  complete source, missingness, and geographic-interpretation guidance.

## 0.7.0

- Added sourced total, land, and water area; coastline; mean elevation; and
  named highest and lowest points.
- Added 188 source-listed major river records across 80 profiles and 187
  source-listed major lake records across 69 profiles.
- Added 240 plain-language climate summaries and represented Köppen-Geiger
  classes for 241 profiles from the 1991–2020 0.1-degree raster.
- Added immutable `ElevationPoint`, `River`, `Lake`, `ClimateZone`,
  `ClimateProfile`, and `PhysicalGeography` models.
- Added physical filters, river/lake discovery helpers, climate-zone discovery,
  physical rankings, discovery-card fields, and five physical flashcard topics.
- Added exact snapshot hashes, reproducible extraction, source coverage gates,
  physical-data validation, and source-role documentation.
- Reworked the documentation opening around offline physical-geography examples
  and added a dedicated interpretation guide.
- Kept country boundary geometry, GeoJSON, bounding boxes, centroids,
  point-in-country lookup, and a separate major-mountain inventory outside this
  release.

## 0.6.0

- Added 234 source-provided national-anthem title profiles without lyrics,
  audio, contributor credits, or adoption histories.
- Added 32 explicitly reviewed source-listed national mottos and published an
  include/exclude decision for every captured statement.
- Added 227 English demonym profiles with source-preserved noun and adjective
  forms.
- Enriched currencies with CLDR English names, common symbols, minor-unit
  digits, and source references.
- Added language names and likely scripts for 722 country-language records,
  using the IANA Language Subtag Registry as a name fallback where needed.
- Added 417 country-level timezone records across 246 profiles and 176
  postal-code formats.
- Added exact currency, language, script, and timezone filters.
- Added typed country rankings for population, area, density, reviewed border
  count, and bundled major-city count.
- Added typed nearest-capital discovery using the existing great-circle
  distance implementation.
- Expanded discovery cards, serialization, source metadata, coverage reports,
  tests, runnable examples, and the public API reference.
- Reworked the documentation opening around useful and educational examples,
  with dedicated country-reference and rankings guides.
- Deferred reference dates, anthem credits/dates, boundary geometry, GeoJSON,
  bounding boxes, centroids, and point-in-country lookup.

## 0.5.0

- Added one sourced local-language identity for all 248 countries and areas,
  spanning 80 languages and 21 writing systems.
- Added pinned Unicode CLDR 48.2 extraction with exact locale/XPath provenance,
  official-language selection metadata, and Unicode License v3 attribution.
- Kept 10 selected UNGEGN records as the higher-evidence national official
  short/formal layer.
- Added sourced English formal names for 240 profiles, including 195 distinct
  long forms, explicit provenance, exact reviewed exceptions, lookup support,
  and honest `None` values for eight areas outside the source intersection.
- Added `Country.formal_name`, `Country.has_distinct_formal_name`, and
  `Atlas.countries_with_formal_names()`.
- Added complete local-name record lookup, formal-name and formal-romanization
  conveniences, evidence kinds, language statuses, and exact source locators.
- Added country coverage discovery with language and script filters.
- Added multilingual examples, coverage reporting, an identity data contract,
  and a clearer official-names documentation guide.
- Established a clear educational and editorial policy for the offline
  geographic dataset, documentation, examples, and contributions.
- Added a community code of conduct, factual-correction guidance, a dedicated
  documentation page, and automated policy and release-content checks.
- Removed an unused entity-classification field. The package now exposes only
  the sourced geographic fields it uses.
- Kept current affairs, opinion, comparisons of people or cultures, and
  speculative narrative outside the bundled dataset.
- Moved national symbols and reference facts to 0.6.0 for their own source review.

## 0.4.0 — Reserved tag; not published to PyPI

- Preserved the public tag after it was created against the 0.3.1 commit before
  the country-identity candidate reached `main`.
- Included the completed country-identity milestone in 0.5.0 rather than moving
  or reusing a public version tag.

## 0.3.1

- Added `Atlas.has_land_route()` for explicit land-graph reachability checks.
- Added `names` and `alpha2_codes` conveniences to `BorderPathResult`.
- Added deterministic `neighbors` and `border_counts` flashcard topics.
- Expanded the border, discovery, API, serialization, and source guides with
  provenance, return-value, connectivity, and edge-case explanations.

## 0.3.0

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

## 0.2.1

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

## 0.1.0

- Rebuilt the project from scratch around a standard-library runtime and one generated SQLite database.
- Added lookup, aliases, standard identifiers, and UN regions for 248 countries and areas.
- Added 241 primary-capital records and 6,265 major-city records from GeoNames.
- Added a separate deterministic source-ingestion project, offline rebuild, tests, wheel demo, and canonical documentation source.
