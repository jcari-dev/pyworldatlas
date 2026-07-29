# Roadmap status

> This file is generated from `build_data/reports/status.json`.

Library version: 0.9.3
Dataset version: 2026.07.22.7
Schema version: 7

Countries and areas: 248 (UN M49 scope)
Capitals: 241 / 248
Capital coordinates: 241 / 241
Populated places: 6265
Local identity names: 248 / 248 countries and areas / 80 languages / 21 scripts
Reviewed national official forms: 10 / official-language selections: 244 / 248
English formal names: 240 / 248 profiles / 195 distinct long forms
Profile fields: 248 population / 247 currency / 245 language-code records
Reference facts: 234 anthem titles / 32 reviewed mottos / 227 English demonym profiles
Practical profiles: 246 timezone profiles / 176 postal formats / 245 currency symbols
Reviewed land borders: 319 / borderless entities: 85
Physical profiles: 240 source profiles / 238 coastlines / 240 elevation-extreme pairs
Named physical features: 188 rivers across 80 profiles / 187 lakes across 69 profiles
Climate: 240 summaries / 241 Köppen-Geiger profiles
Last validation: PASS

| Milestone | Version | Status | Implemented functions | Tests | Dataset coverage | Documentation | Release |
|---|---:|---|---|---|---|---|---|
| 0 — Clean foundation | 0.1.0 | complete | Standard package layout, generated database, release automation | Local 0.1.0 release gate passed | Captured and checksummed source snapshots | Sphinx source and maintainer instructions | Rebuilt baseline tagged v0.1.0 |
| 1 — Generated country core | 0.1.0 | complete | Lookup, search, collection protocol, capitals, populated places, dataset info | Python 3.10-3.14 CI and local release gate passed | 248 countries and areas / 241 capitals / 6265 places | Core usage and data guides | Included in the v0.1.0 rebuilt baseline |
| 2 — Country profiles, coordinates, and discovery | 0.2.1 | complete | Profiles, coordinate tools, flags, discovery cards, stable samples, flashcards | Unit tests and complete local release gate pass | 248 profiles / 6,265 coordinate-bearing places / 5 reviewed local names | Profile, local-name, coordinate, and discovery guides | Publication state is tracked on GitHub Releases and PyPI |
| 3 — Reviewed land borders | 0.3.0 | complete | Neighbors, shared borders, shortest land paths, crossings, components, and borderless entities | Source-difference review gate, graph invariants, API tests, and complete release gate | 319 reviewed undirected land-border relationships | Border API, data policy, exceptions, and examples | Publication state is tracked on GitHub Releases and PyPI |
| 3.1 — Border API and learning polish | 0.3.1 | complete | Land-route reachability, path name/code conveniences, neighbor flashcards, and border-count flashcards | Deterministic flashcard fixtures, reachability edge cases, examples, and complete release gate | No dataset change; derives from the 319 reviewed relationships | API provenance, connectivity semantics, serialization, flashcards, and examples | Publication state is tracked on GitHub Releases and PyPI |
| 4 — Official country identity | 0.4.0 | complete | Complete local display names, English formal names, reviewed local official forms, language/script lookup, romanization, and coverage discovery | 30 unit/pipeline tests, 221 doctests, clean-wheel examples, and release audit passed | 248 local identities / 240 English formal names / 10 reviewed local official forms | Identity guide, fun multilingual examples, evidence levels, source rules, and complete coverage metrics | Included in published v0.5.0 |
| 5 — Educational scope and publication safety | 0.5.0 | complete | Editorial policy, public-field scope audit, respectful contribution and correction process, and policy release checks | Policy-document integrity, public-model scope, source-role, example-language, documentation, and release audits | Reviewed geographic dataset with updated provenance and policy metadata; no new narrative fields | Educational purpose, source scope, geographic conventions, community standards, and correction guidance | Published as v0.5.0 |
| 6 — Country reference and discovery | 0.6.0 | complete | Anthem titles, reviewed mottos, demonyms, complete timezone profiles, postal formats, richer currency and language metadata, profile filters, rankings, and nearest capitals | Source-scope, review-decision, typed-model, ranking, filtering, serialization, documentation, and clean-wheel release gates | 234 anthem profiles / 32 reviewed mottos / 227 demonym profiles / 246 timezone profiles / 176 postal formats / 722 country-language records | Reference-facts guide, example gallery, rankings, filters, provenance, coverage boundaries, and runnable examples | Published as v0.6.0 |
| 7 — Physical geography | 0.7.0 | complete | Land and water area, coastline, elevation extremes, major rivers and lakes, climate summaries, Köppen-Geiger classes, physical filters, and rankings | Pinned-source coverage, typed-model, physical discovery, ranking, serialization, documentation, and release gates | 240 physical profiles / 188 rivers / 187 lakes / 241 Köppen-Geiger profiles | Physical profile guide, climate methodology, coverage rules, rankings, API reference, and runnable examples | Published as v0.7.0 |
| 8 — Education and usability | 0.8.0 | complete | Readable country summaries, city-name and proximity discovery, coordinate display helpers, discoverable learning topics, and deterministic multiple-choice questions | Public API behavior, deterministic quiz construction, coordinate formatting, city discovery, serialization, examples, browser runtime, documentation, and supported-Python release gates | Reuses the complete reviewed 0.7 dataset without changing schema or coverage | Learning guide, classroom recipes, refreshed playground, usability examples, polished docstrings, and complete API reference | Published as v0.8.0 |
| 9 — Optional interactive maps | 0.9.0 | complete | Optional offline 3D elevation and climate maps, browser display, HTML export, river overlays, and capital markers | Complete map-pack coverage, record integrity, viewer controls, offline HTML, clean-wheel rendering, documentation, and release gates | 248 Overview maps / 248 Standard maps from pinned elevation, climate, outline, and river snapshots | Map-edition guide, installation choices, viewer API, source limits, examples, and release instructions | Published in v0.9.0 |
| Stable offline atlas | 1.0.0 | planned | — | — | — | — | — |
