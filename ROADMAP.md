# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: 0.9 — Optional interactive maps

Version 0.9 adds optional offline 3D elevation and climate maps for all 248
existing profiles. Overview and Standard data editions install separately, so
the core atlas remains small and dependency-free. The release adds no boundary
geometry, GeoJSON, or point-in-country public API.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next milestone: stable-API hardening

The next milestone concentrates on consistency, performance, documentation
coverage, typing, packaging, and full release-candidate testing. Its purpose is
to remove surprises before the stable contract rather than introduce another
broad data surface.

## 1.0 — Stable offline atlas

Version 1.0 represents a documented, dependable public API with reproducible
data builds, supported upgrade guidance, and complete release automation.

## Deferred work

Boundary geometry, GeoJSON export, bounding boxes, polygon centroids, and
point-in-country lookup remain outside the current plan. They add meaningful
licensing, modeling, and boundary-interpretation work and may be better suited
to an optional post-1.0 extension. The 0.9 viewer uses generalized outlines
internally but does not publish their coordinates as geographic boundary data.

Anthem lyrics, audio, contributor histories, and adoption dates also remain
outside the current data contract.
