# Roadmap

PyWorldAtlas grows through small, installable releases with explicit data,
documentation, and compatibility boundaries. Planned work is not part of the
public API until it is implemented, tested, documented, and published.

## Current release: Friendly by default (0.13)

Version 0.13 makes the atlas easier to use: one naming style, results that
print as one clear line, "did you mean" suggestions, built-in help, world maps
of statistics, a cheat sheet, quests, a glossary, "Try it" links, and dark
mode in the docs. Version 0.12 added an optional statistics pack of eleven
World Bank indicators since 1960 and an optional landmarks pack. Neither
release adds boundary geometry, GeoJSON, or a point-in-country public API.

The complete shipped coverage is generated in the
[roadmap status](docs/project/ROADMAP_STATUS.md).

## Next releases

The next releases each ship one large theme, on the way to 1.0:

- **The encyclopedia (0.14):** generated reference entries built only from
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
