# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: 0.8 — Education and usability

Version 0.8 makes the existing offline atlas easier to explore and teach. It
adds readable country summaries, partial and nearby-city discovery, friendly
coordinate labels, compass directions, discoverable learning topics, and
deterministic multiple-choice questions. The release reuses the complete 0.7
dataset and does not change its schema or source scope.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next milestone: 0.9 — Stable-API hardening

Version 0.9 is reserved for consistency, performance, documentation coverage,
typing, packaging, and full release-candidate testing. Its purpose is to remove
surprises before the stable contract rather than introduce a broad new data
surface.

## 1.0 — Stable offline atlas

Version 1.0 represents a documented, dependable public API with reproducible
data builds, supported upgrade guidance, and complete release automation.

## Deferred work

Boundary geometry, GeoJSON export, bounding boxes, polygon centroids, and
point-in-country lookup remain outside the current plan. They add meaningful
package size, licensing, modeling, and boundary-interpretation work and may be
better suited to an optional post-1.0 extension. They are not scheduled for 0.8.

Anthem lyrics, audio, contributor histories, and adoption dates also remain
outside the current data contract.
