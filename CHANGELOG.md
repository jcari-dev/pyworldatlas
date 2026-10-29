# Changelog

## Unreleased

- **World maps of statistics:** `Atlas.world_map("life_expectancy")` and
  `pyworldatlas world-map life_expectancy` color every country by one
  statistic, for its latest year or a chosen one. The map is plain SVG on the
  Equal Earth projection, needs no download when it opens, follows light and
  dark mode, and comes with a summary and a table of every value for screen
  readers. Needs the statistics pack and a map pack.
- **Did you mean...?** Mistyped countries, places, cities, quiz topics, and
  indicators now suggest the closest names, such as "No country matches
  'Japn'. Did you mean Japan?".
- **Friendlier learning calls:** `atlas.quiz("capitals")` and
  `atlas.flashcards("capitals")` take the topic first and ask 5 questions or
  make 10 cards by default. Topics and indicators accept any case, spaces,
  and singular or plural forms ("Capital", "life expectancy").
- **Results that read well:** printing any result gives one clear line, such
  as `#1 Russia: 17,098,242 km²`, `Seoul, South Korea · 1,153 km`, or
  `France → Germany → Poland → Russia → China (4 border crossings)`, and the
  REPL shows short reprs instead of nested objects. Quiz questions print with
  numbered choices.
- **Every result reads well**, including areas, climate, currencies, time
  zones, anthems, and dataset info, such as `Area('377,915 km², 3.55%
  water')` or `Timezone('Asia/Tokyo, UTC+9')`.
- **`pyworldatlas.show_details()`** prints every field instead of the short
  form, for the whole session or inside a `with` block; the environment
  variable `PYWORLDATLAS_DETAILS=1` turns it on from the start.
- **Distances:** `distance_between` and every "nearest" result return a
  `Distance`, a number that prints with its unit (`9,713 km`) and still works
  in arithmetic and JSON.
- **Sun times on the local clock:** `atlas.sun("Paris")` uses the local time
  of a city, capital, or country when the computer has time zone data
  (`SunTimes.timezone_id`, `local_sunrise`, `local_sunset`), and UTC otherwise.
- **Tidy numbers:** whole measurements are whole numbers (`3776`, not
  `3776.0`), and the water share of an area is rounded to two decimals.
- **`country.summary` is a property**, like every other `summary`; calling it
  as `country.summary()` still works.
- **One name for country codes:** statistics and country references also offer
  `country_code`.
- **Fixed:** the land-border methods (`neighbors`, `shares_border`,
  `border_path`, and the rest) accept a `Country` as well as a name or code,
  instead of failing with a database error.

## 0.12.1

A more welcoming atlas, honest licensing, and up-to-date documentation.

- **Welcome:** the documentation home page opens with a "Look up anything"
  search box that answers in the playground, and starting points for
  students, teachers, and developers. A new "Teaching with PyWorldAtlas" guide
  offers a 15-minute lesson and a printable class quiz with its answer key.
- **Playground:** **Surprise me** shows a famous place, **Quiz me** asks five
  questions with answer buttons and a score, and three challenge recipes find
  the shortest December day, the capitals closest to the equator, and the two
  capitals farthest apart.
- **Shorter pages:** the README is a third of its old length, the main guides
  open with an "In 30 seconds" example, guides show real output, and every
  code block has a Copy button that copies only the code.
- **Maps:** place markers rest on the ground, small islands sit at sea level,
  and the blue layer is renamed "Water and ice". The map animation shows the
  place layers.
- **Quizzes:** place quizzes use only mountains of 3,000 m and higher.
- **Licensing:** the package metadata reads
  `MIT AND CC-BY-4.0 AND Unicode-3.0 AND CC0-1.0`, and the wheel includes the
  CC BY 4.0 text and the third-party notices, which list every source, its
  terms, and the changes made.
- **Removed:** six fields that were always empty (`Area.disputed_km2`,
  `Geography.centroid`, `CountryCodes.wikidata`, `Capital.largest_city`,
  `Capital.alternate_names`, `City.alternate_names`) and the `include_history`
  argument of `Country.to_dict` and `to_json`, which had no effect.
- **Package page and docs:** a new description, keywords, and classifiers,
  and documentation that covers every feature and data pack.

## 0.12.0

The world in numbers, landmarks, and a new playground.

- New optional **statistics** pack (about 150 KB): eleven basic World Bank
  indicators for every country since 1960 (CC BY 4.0, credited): population,
  population density, urban population, life expectancy, birth and death
  rates, forest and agricultural land, access to electricity and drinking
  water, and internet use. Missing years stay missing.
- `Atlas.time_series`, `Atlas.statistic`, `Atlas.sort_by_statistic`, and
  `Atlas.indicators`; `StatisticSeries.sparkline()` draws a one-line chart and
  `summary` describes the change in a sentence. New `pyworldatlas stat`
  command and "The world in numbers" guide.

- New playground: **Look up anything** answers any country or place in plain
  cards (facts, nearby places, daylight), and **Open in the editor** loads the
  Python behind each card. Four new recipes cover places, the sun, travel
  basics, and one search for everything.
- New optional **landmarks** pack (about 150 KB): 4,010 airports with
  scheduled flights (OurAirports, public domain) and 1,266 UNESCO World
  Heritage sites (Wikidata, CC0). `Atlas.airport`, `Atlas.airports`,
  `Atlas.world_heritage_sites`, `Atlas.world_heritage_site`,
  `Atlas.world_heritage_sites_near`, and the `pyworldatlas airport` and
  `pyworldatlas heritage` commands.
- New `PackNotInstalledError` names the command that installs a missing pack.
- Lower memory: the first search after installing the place packs now peaks
  near 280 MB for the world pack (was about 520 MB for the explorer pack), so
  every pack fits a computer with 512 MB, such as a Raspberry Pi Zero 2 W
  (measured on a desktop computer).
- Faster start: compression, hashing, and pack modules load on first use.
- New: `Atlas.place_quiz` asks about famous places: what kind of place it is,
  which of two mountains is higher, and which of two places is closer to the
  equator. Answers come from the data; seeds make lessons repeatable.
- New: `Atlas.antipode` and `pyworldatlas antipode` find the point straight
  through the Earth from any place, and the places nearest it.

## 0.11.1

- New: travel basics for 245 countries and areas. `Country.travel` gives plug
  types (IEC letters A to N), the household mains voltage and frequency, and
  the side of the road people drive on, from CC0 Wikidata statements. A value
  stays missing when the source does not agree. Country summaries show a
  "Travel" line.
- New learning topics for flashcards and quizzes: `driving_sides`,
  `plug_types`, and `mains_electricity`.
- New: `Atlas.sun` and `pyworldatlas sun` give sunrise, sunset, day length,
  and the noon sun height for any place and date, worked out offline with the
  NOAA solar equations. A new "Sun and seasons" guide shows why seasons happen.
- Dataset `2026.10.27.1`, schema 8.

## 0.11.0

Every place on Earth.

- New: search every place on Earth. Every install now includes a school atlas
  of 207,664 places chosen by educational value (about 2 MB): every country,
  region, and town of 5,000 people or more, plus the mountains, volcanoes,
  lakes, rivers, deserts, islands, and landmarks that people around the world
  know. `Atlas.search_places`, `Atlas.place`, and `Atlas.places_near` find
  places by local or English name, best known first, and list the nearest
  places to any point.
- New optional packs `places-explorer` and `places-world` add every other
  place in the GeoNames gazetteer, 11 million places in all.
- New `Place` and `PlaceDistance` models, `Atlas.place_kinds()` and
  `Atlas.place_categories()`, and the `pyworldatlas place` and
  `pyworldatlas near` commands.
- New: `Atlas.lookup` and `pyworldatlas find` search countries, cities,
  regions, and landmarks in one call. A country named exactly comes first as
  its full profile, then the best-known places.
- New: 3D maps mark the country's best-known towns, mountains and islands,
  lakes and seas, and landmarks, each kind a layer with its own shape, color,
  and show or hide toggle (`Atlas.map(..., places=8)`). The screen-reader
  description lists every marked place.
- New: `Atlas.places_in` lists the best-known places in a country.
- New: the map page has a **Find a place** box that labels any marked place on
  the map and announces it to screen readers.
- A short reviewed list corrects English names misspelled in the source, such
  as GeoNames' "Amazone River", now "Amazon River".
- Places are stored in a compact column format (6 to 10 bytes per place) using
  only the standard library, and unpacked once into a local SQLite index on
  first search.

## 0.10.0

A big step toward 1.0. The public API is now guarded by a snapshot test, so
any change to it is deliberate and listed here.

- In Jupyter and other notebooks, a `Country` now displays as an accessible
  fact card that follows the notebook's theme.
- Speed guards in the test suite fail if common calls, the first load, or the
  import slow down sharply, and CI now also tests Windows and macOS.
- Country lookup understands everyday names: "UK", "Britain", "Burma", "UAE",
  "DRC", "Cape Verde", "East Timor", "Swaziland", "Macau", "Falklands",
  "Bosnia", and more, plus spellings with or without a leading "The" and "St"
  for "Saint". Parts of countries and ambiguous names ("England", "Korea") are
  still not guessed.
- Made repeated lookups much faster: every `Atlas` now keeps its own country,
  border, code, and place caches, so profiles are read at most once. Ranking by
  border count, neighbor quizzes, and nearest-place searches drop from hundreds
  of milliseconds to a few milliseconds on a typical laptop.
- Loading the full collection now reads each related table once instead of
  issuing several queries per country.
- Fixed closing one `Atlas` clearing the cached profiles of every other open
  `Atlas`.
- Reduced import time by loading `importlib.resources` and `hashlib` only when
  they are needed.
- Climate quiz answers now read `Af: Tropical, rainforest` instead of using a
  dash separator.
- The package is now marked as typed (`py.typed`), so editors and type
  checkers see its full annotations; the source passes strict mypy.
- Added `python maintain.py quality` with Ruff, strict mypy, and branch coverage
  (currently 92%, minimum 90%) using development-only tools from
  `requirements-dev.txt`.
- Split the 1,200-line models module into a `pyworldatlas.models` package
  with small topic modules, and moved profile building, flashcard helpers, and
  ranking metrics out of `atlas.py`. Every import path and signature is
  unchanged.
- Added a public API snapshot test that fails whenever an exported name,
  signature, field, or method changes without an intentional update.
- Fixed broken inline-code formatting in the `rank_countries` docstring.
- **Maps with zero dependencies.** The 3D map viewer is now part of
  PyWorldAtlas and builds maps with the standard library only; Plotly is no
  longer required. Map data installs as a checksummed data pack with
  `pyworldatlas get maps` (Standard) or `pyworldatlas get maps-lite` (Overview),
  or offline from a file with `pyworldatlas add`. All 496 maps (248 profiles in
  both qualities) are identical to the 0.9 output.
- Added `pyworldatlas packs` and `pyworldatlas remove`, the `pyworldatlas.packs`
  module, and `Atlas(data_dir=...)` for choosing the pack folder.
- `CountryMap` moved to `pyworldatlas.maps` and gained `to_dict()`; `figure()`
  still returns a Plotly figure when the separate `plotly` package is installed.
- Redesigned the map page: the map fills the window beside one clear control
  panel (color, terrain height, labels and rivers, motion, reset, Save PNG),
  with a country badge and subtitle, light and dark themes, and a bottom-sheet
  layout on phones. `to_dict()` and `figure()` keep Plotly's in-figure controls
  for notebooks.
- **Accessibility.** Map pages can be used without a mouse or a screen: the map
  takes keyboard focus (arrow keys turn and tilt it, plus and minus zoom, 0
  resets), carries a plain-language description of its terrain, climate
  classes, capital, and rivers for screen readers (also shown under "About
  this map"), and announces every control change. Control outlines now meet
  the 3:1 contrast requirement in light and dark themes.
- The documentation adds a "Skip to main content" link and darker link, label,
  and caption colors that meet WCAG AA contrast.
- The `pyworldatlas-mapview` and `pyworldatlas-mapdata-*` packages are retired.
  The `maps` and `maps-overview` extras remain, empty, so older install commands
  still work.
- Published the release plan, generated `llms.txt` and `llms-full.txt` plain-text
  documentation indexes, and removed em-dashes from the project text.

## 0.9.5

- Added an installed `pyworldatlas` command with version, country lookup,
  search, dataset metadata, JSON output, and concise error messages.
- Distinguished missing country queries from genuinely ambiguous exact names,
  and added regression coverage for both outcomes.
- Strengthened clean-wheel checks so the console command and module command
  are exercised from the built artifact before release.
- Reviewed the public documentation, examples, docstrings, package metadata,
  repository guidance, and release instructions for accuracy and readability.

## 0.9.4

- Added play, pause, and adjustable-speed rotation controls to standalone 3D
  maps while respecting reduced-motion preferences.
- Added an explicit high-resolution PNG download for the current map view and
  configured Plotly's existing image action to use the same crisp output.
- Added `auto_rotate` and `rotation_speed` options to HTML export and
  browser display without changing map data or core-package dependencies.
- Added a maintainer GIF utility for producing optimized project-page
  animations from real map figures.
- Expanded the README, map guide, API documentation, and release tests around
  motion, export, accessibility, and documentation media.

## 0.9.3

- Reorganized the API reference around common tasks and gave every generated
  class, method, and property a consistent, readable layout.
- Clarified first-time installation, optional map editions, and the separate
  command for upgrading an existing installation.
- Refreshed the Explore section and polished the shared GitHub and PyPI project
  page without changing the public API or dataset.
- Kept documentation deployment aligned with PyPI so the browser playground
  never advertises an unpublished package version.

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

## 0.4.0 (reserved tag, not published to PyPI)

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

## 0.2.0 (unpublished candidate)

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
