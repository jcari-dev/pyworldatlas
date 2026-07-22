# PyWorldAtlas 0.3.1 release status

Version 0.3.1 is a focused border API and learning-tools patch built on the
published 0.3.0 land-border release. It changes no country record, reviewed
border relationship, database schema, or dataset version.

## Public API additions

- `Atlas.has_land_route(origin, destination)` returns whether two countries or
  areas belong to the same accepted land-border component.
- `BorderPathResult.names` returns the route's country names in path order.
- `BorderPathResult.alpha2_codes` returns its alpha-2 codes in path order.
- `Atlas.flashcards()` accepts the deterministic `neighbors` and
  `border_counts` topics.

`has_land_route()` describes graph reachability only. It does not claim that a
road exists or provide information about border access, visas, ferries, or
current travel conditions. An entity is reachable from itself with zero border
crossings.

Neighbor flashcards exclude entities without an accepted land-border edge
because those cards would have no neighbor answer. Border-count cards include
them and answer `0`.

## Dataset and compatibility

- Library version: `0.3.1`
- Schema version: `3`
- Dataset version: `2026.07.21.1`
- Reviewed border relationships: `319`
- Runtime dependencies: `0`
- Supported Python versions: 3.10 through 3.14

All new values are derived from the graph published in 0.3.0. No additional
geographic source claim is introduced by this patch.

## Documentation and tests

The border guide now maps every public method to its result type and explains
stored relationships versus derived results. The API, discovery, serialization,
quick-start, source, and example material cover the new conveniences and their
edge cases.

Runtime tests cover connected, disconnected, and same-entity reachability;
deterministic graph flashcards; route names and codes; serialization; and all
existing graph invariants.

## Release gate

Before tagging, run this command from a clean checkout:

```console
python maintain.py prepare-release 0.3.1
```

The gate runs runtime and pipeline tests, builds the wheel and source
distribution, installs and executes every example from the wheel, builds HTML
and doctest documentation with warnings treated as errors, and audits wheel
contents. Publication uses the `v0.3.1` tag workflow in `RELEASING.md`.
