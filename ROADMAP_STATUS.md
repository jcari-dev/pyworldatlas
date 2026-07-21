# Roadmap status

> This file is generated from `build_data/reports/status.json`.

Library version: 0.3.0
Dataset version: 2026.07.21.1
Schema version: 3

Countries and areas: 248 (UN M49 scope)
Capitals: 241 / 248
Capital coordinates: 241 / 241
Populated places: 6265
Official local names: 5 across 2 reviewed countries
Profile fields: 248 population / 247 currency / 245 language-code records
Reviewed land borders: 319 / borderless entities: 85
Last validation: PASS

| Milestone | Version | Status | Implemented functions | Tests | Dataset coverage | Documentation | Release |
|---|---:|---|---|---|---|---|---|
| 0 — Clean foundation | 0.1.0 | complete | Standard package layout, generated database, release automation | Local 0.1.0 release gate passed | Captured and checksummed source snapshots | Sphinx source and maintainer instructions | Rebuilt baseline tagged v0.1.0 |
| 1 — Generated country core | 0.1.0 | complete | Lookup, search, collection protocol, capitals, populated places, dataset info | Python 3.10-3.14 CI and local release gate passed | 248 countries and areas / 241 capitals / 6265 places | Core usage and data guides | Included in the v0.1.0 rebuilt baseline |
| 2 — Country profiles, coordinates, and discovery | 0.2.1 | complete | Profiles, coordinate tools, flags, discovery cards, stable samples, flashcards | Unit tests and complete local release gate pass | 248 profiles / 6,265 coordinate-bearing places / 5 reviewed local names | Profile, local-name, coordinate, and discovery guides | Publication state is tracked on GitHub Releases and PyPI |
| 3 — Reviewed land borders | 0.3.0 | complete | Neighbors, shared borders, shortest land paths, crossings, components, and borderless entities | Source-difference review gate, graph invariants, API tests, and complete release gate | 319 reviewed undirected land-border relationships | Border API, data policy, exceptions, and examples | Publication state is tracked on GitHub Releases and PyPI |
| 4 — Geometry | 0.4.0 | planned | — | — | — | — | — |
| 5 — Statistics | 0.5.0 | planned | — | — | — | — | — |
| 6 — Leaders | 0.6.0 | planned | — | — | — | — | — |
| 7 — Culture and institutions | 0.7.0 | planned | — | — | — | — | — |
| 8 — Advanced education and export | 0.8.0 | planned | — | — | — | — | — |
| 9 — Full-world hardening | 0.9.0 | planned | — | — | — | — | — |
| Stable offline atlas | 1.0.0 | planned | — | — | — | — | — |
