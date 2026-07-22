Roadmap and visible progress
============================

Each release has a defined feature boundary, dataset scope, test gate, and
documentation update.

.. list-table:: Release train
   :header-rows: 1
   :widths: 14 24 46 16

   * - Version
     - Status
     - Visible improvement
     - Release state
   * - 0.1.0
     - Complete
     - 248-country-and-area core, lookup, 241 capitals, 6,265 cities, documentation
     - Rebuilt baseline tagged
   * - 0.2.1
     - Complete
     - Rich profiles, coordinate tools, flags, discovery cards, stable samples, flashcards
     - Published
   * - 0.3.0
     - Complete
     - 319 reviewed land borders, neighbors, shared neighbors, paths, connected components
     - Published
   * - 0.3.1
     - Complete
     - Reachability, path conveniences, graph flashcards, expanded API guidance
     - Published
   * - 0.4.0
     - In progress
     - Complete selected local identities, 240 English formal names, scripts, provenance, coverage discovery
     - Local release gate passed; publication pending
   * - 0.5.0
     - Planned
     - Anthem titles, mottos, contributors, adoption dates, and labelled civic events
     - —
   * - 0.6.0
     - Planned
     - Boundary geometry, point-in-boundary lookup, GeoJSON
     - —
   * - 0.7.0
     - Planned
     - Historical statistics and sourced institutions
     - —
   * - 0.8.0
     - Planned
     - Advanced learning utilities, exports, expanded CLI
     - —
   * - 0.9.0
     - Planned
     - Full-world validation, refresh automation, and release hardening
     - —
   * - 1.0.0
     - Planned
     - Stable offline atlas
     - —

Release boundary
----------------

The 0.1.0 source state established the rebuilt runtime and dataset baseline.

Version 0.2.1 exposes population and currency context,
language and calling-code metadata, top-level domains, observed timezones,
capital coordinates, exact city lookup, and great-circle distance, bearing, and
midpoint calculations. It also retains the verified Brazil/Switzerland UNGEGN
local-name pilot and adds flag emoji, calculated density, discovery cards,
stable sampling, and structured flashcards.

Version 0.3.0 added a reviewed land-border graph, neighbor and shared-neighbor
queries, deterministic shortest paths, crossing counts, connected land regions,
and borderless-entity discovery. Version 0.3.1 adds explicit reachability,
path-name and alpha-2-code conveniences, graph-derived flashcards, and expanded
API provenance guidance.

Version 0.4.0 adds one sourced local identity for all 248 countries and areas,
covering 80 languages and 21 scripts through pinned CLDR 48.2 data. Reviewed
UNGEGN replacements add national official short/formal names and
source-provided romanization for 10 selected records. A separate sourced
English formal-name layer covers 240 profiles, with eight explicit source-scope
gaps. The milestone remains in development until the candidate is committed,
reviewed, and published.

Version 0.5.0 adds national-symbol and civic-fact models after their source
matrix is approved. Boundary geometry, border lengths, point-in-country lookup,
and GeoJSON move to 0.6.0.
