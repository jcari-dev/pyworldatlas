# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: Optional interactive maps (0.9)

Version 0.9 adds optional offline 3D elevation and climate maps for all 248
existing profiles. Overview and Standard data editions install separately, so
the core atlas remains small and dependency-free. Patch releases also tighten
installed-package usability, documentation, and release checks. The release
adds no boundary geometry, GeoJSON, or point-in-country public API.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next milestone: Stable and instant (1.0)

Version 1.0 represents a documented, dependable public API with reproducible
data builds, supported upgrade guidance, and complete release automation. It
concentrates on consistency, performance, typing, packaging, and full
release-candidate testing rather than another broad data surface. It also
introduces a single-package installation model in which optional data, such as
map editions, installs as checksummed data packs.

## The 1.x series

The 1.x series ships a few large, themed releases:

- **Every place on Earth (1.1):** optional places and landmarks packs, travel
  basics, one lookup across all place types, and proximity search.
- **The world in numbers (1.2):** an optional statistics pack of official
  indicators, each with unit, reference year, and source.
- **The encyclopedia (1.3):** generated reference entries built only from
  sourced data, and an offline static-site export.

Every addition follows the data-admission rules in the
[1.x plan](docs/project/PLAN_1_X.md): public, openly licensed, traceable,
factual sources only.

## Deferred work

Boundary geometry, GeoJSON export, bounding boxes, polygon centroids, and
point-in-country lookup remain outside the current plan. They add meaningful
licensing, modeling, and boundary-interpretation work and may be better suited
to an optional post-1.0 extension. The 0.9 viewer uses generalized outlines
internally but does not publish their coordinates as geographic boundary data.

Anthem lyrics, audio, contributor histories, and adoption dates also remain
outside the current data contract.
