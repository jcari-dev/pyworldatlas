# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: 0.7

Version 0.7 completes the first rich offline country profile. It includes
country identity and local names, capitals and major cities, coordinates and
distance tools, reviewed land neighbors, practical reference facts, physical
geography, climate classes, rankings, and deterministic learning tools.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next milestone: 0.8 — Education and usability

The 0.8 goal is to make the existing atlas easier and more enjoyable to use,
especially for learners and teachers. The highest-value candidates are:

- Simple city search and nearby-city discovery.
- Clear, readable country summaries for terminals, notebooks, and lessons.
- Friendly coordinate helpers for common geography activities.
- Deterministic multiple-choice questions built from sourced facts.
- Beginner-focused examples, classroom recipes, and playground improvements.
- API naming, error-message, typing, accessibility, and browser-runtime polish.

This milestone should reuse the validated dataset wherever possible. Any new
field still requires the same source, license, coverage, and neutrality review
as earlier releases.

## 0.9 — Hardening for a stable API

Version 0.9 is reserved for consistency, performance, documentation coverage,
typing, packaging, and full release-candidate testing. Its purpose is to remove
surprises before the stable contract rather than introduce a large new data
surface.

## 1.0 — Stable offline atlas

Version 1.0 represents a documented, dependable public API with reproducible
data builds, supported upgrade guidance, and complete release automation.

## Deferred work

Boundary geometry, GeoJSON export, bounding boxes, polygon centroids, and
point-in-country lookup are not scheduled for 0.8. They add meaningful package
size, licensing, modeling, and boundary-interpretation work and may be better
suited to an optional post-1.0 extension.

Anthem lyrics, audio, contributor histories, and adoption dates also remain
outside the current data contract.
