# PyWorldAtlas 0.3.0 release status

Version 0.3.0 is the reviewed land-border release. It preserves the 248-entity
UN M49 scope and the profile, coordinate, city, and learning APIs from 0.2.1.

## Public API

- `Atlas.neighbors(country)`
- `Atlas.shares_border(country1, country2)`
- `Atlas.shared_neighbors(country1, country2)`
- `Atlas.border_path(origin, destination)`
- `Atlas.border_crossings(origin, destination)`
- `Atlas.countries_reachable_by_land(country)`
- `Atlas.countries_with_no_land_borders()`
- Immutable, serializable `BorderPathResult`

## Dataset and review boundary

- 319 canonical undirected land-border relationships.
- 315 relationships confirmed by both pinned GeoNames and Natural Earth inputs.
- Four explicit inclusions and two exclusions in
  `build_data/reviewed/border_decisions.csv`.
- 85 countries and areas with no accepted land-border edge.
- Schema version 3 and dataset version `2026.07.21.1`.

The build rejects unknown endpoints, self-edges, duplicate pairs, unexpected
source counts, and any source difference without an explicit decision. Runtime
tests cover symmetry, borderless entities, unreachable routes, zero-crossing
paths, and every edge in a returned path.

## Deliberate exclusions

Version 0.3.0 does not include polygon or line geometry, border length, maritime
boundaries, point-in-country lookup, GeoJSON, road routing, or travel advice.
These are not implied by the graph API.

## Release gate

Before tagging, the following command must pass from a clean checkout:

```console
python maintain.py prepare-release 0.3.0
```

The gate runs runtime and pipeline tests, builds the wheel and source
distribution, installs and executes every example from the wheel, builds HTML
and doctest documentation with warnings treated as errors, and audits wheel
contents. Publication uses the existing `v0.3.0` tag workflow documented in
`RELEASING.md`.
