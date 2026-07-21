Roadmap and visible progress
============================

Each milestone must remain installable, tested, documented, and honest about
coverage. Later features are not merged into the README before they work.

.. list-table:: Release train
   :header-rows: 1
   :widths: 14 24 46 16

   * - Version
     - Status
     - Visible improvement
     - Release state
   * - 0.1.0
     - Released
     - 248-country-and-area core, lookup, 241 capitals, 6,265 cities, documentation
     - PyPI, GitHub Release, and public documentation
   * - 0.2.0
     - In progress
     - Rich profiles, city coordinates, distances, bearings, midpoints, local-name pilot
     - Runtime and dataset implementation complete; release gate in progress
   * - 0.3.0
     - Not started
     - Borders, neighbors, shared neighbors, border paths
     - —
   * - 0.4.0
     - Not started
     - Geometry, coordinate lookup, GeoJSON
     - —
   * - 0.5.0
     - Not started
     - Population, GDP, indicator history, comparison and ranking
     - —
   * - 0.6.0
     - Not started
     - Heads of state, heads of government, monarchs
     - —
   * - 0.7.0
     - Not started
     - Languages, currencies, timezones, communication and culture
     - —
   * - 0.8.0
     - Not started
     - Quizzes, calculated facts, exports, expanded CLI
     - —
   * - 0.9.0
     - Not started
     - Full-world validation, refresh automation, and release hardening
     - —
   * - 1.0.0
     - Not started
     - Stable offline atlas
     - —

Current release boundary
------------------------

Release 0.1.0 is public. Tests, clean-wheel installation, examples, HTML
documentation, doctests, and wheel-content auditing pass. CI covers Python 3.10
through 3.14, and the wheel, source distribution, checksums, release manifest,
PyPI page, GitHub Release, and public documentation are available.

The unreleased 0.2.0 checkout now exposes population and currency context,
language and calling-code metadata, top-level domains, observed timezones,
capital coordinates, exact city lookup, and great-circle distance, bearing, and
midpoint calculations. It also retains the verified Brazil/Switzerland UNGEGN
local-name pilot. Borders and border paths are reserved for 0.3.0.
