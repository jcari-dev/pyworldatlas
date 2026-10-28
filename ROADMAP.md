# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: Every place on Earth (0.11)

Version 0.11 adds every place on Earth: a school atlas of 207,664 places in
every install, 11 million places with the optional place packs, one search
across countries and places, and places on the 3D maps. Version 0.10 made the
public API stable, typed, and instant, with zero-dependency maps. Neither
release adds boundary geometry, GeoJSON, or a point-in-country public API.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next releases

The next releases each ship one large theme, on the way to 1.0:

- **More of every place (0.11.x):** travel basics (plugs, mains supply, and
  driving side) and more landmark detail.
- **The world in numbers (0.12):** an optional statistics pack of official
  indicators, each with unit, reference year, and source.
- **The encyclopedia (0.13):** generated reference entries built only from
  sourced data, and an offline static-site export.

Every addition follows the data-admission rules in the
[release plan](docs/project/PLAN.md): public, openly licensed, traceable,
factual sources only.

## Deferred work

Boundary geometry, GeoJSON export, bounding boxes, polygon centroids, and
point-in-country lookup remain outside the current plan. They add meaningful
licensing, modeling, and boundary-interpretation work and may be better suited
to an optional post-1.0 extension. The 0.9 viewer uses generalized outlines
internally but does not publish their coordinates as geographic boundary data.

Anthem lyrics, audio, contributor histories, and adoption dates also remain
outside the current data contract.
