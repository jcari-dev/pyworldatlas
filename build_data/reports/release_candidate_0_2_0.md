# PyWorldAtlas 0.2.0 release-candidate evidence

Version 0.2.0 is locally release-ready as the rich-profile and coordinate
milestone. Production publication remains a separate maintainer action.

## Shipped capability

- 248 immutable country and area profiles.
- Population snapshots on 248 profiles.
- Currency metadata on 247 profiles.
- Language codes on 245 profiles.
- Calling codes on 243 profiles.
- Top-level domains on all 248 profiles.
- 241 primary-capital coordinate records and 6,265 coordinate-bearing city rows.
- Exact city lookup with explicit ambiguity errors.
- Validated latitude and longitude.
- Great-circle distance in kilometres, miles, and nautical miles.
- Initial bearings and spherical midpoints.
- Named-place, typed-model, country-capital, and raw-coordinate distance inputs.
- Flag emoji on all 248 country and area profiles.
- Calculated population density with explicit missing-value behavior.
- Immutable discovery cards and compact country references.
- Deterministic country sampling with continent and region filters.
- Structured educational flashcards across 16 documented topics.
- Five visually verified UNGEGN local names across the Brazil/Switzerland pilot.

## Quality gate

| Check | Result |
|---|---:|
| Unit tests | 25 passing |
| Sphinx doctests | 157 passing |
| Complete playground data audit | Passing |
| Deterministic database rebuild | Passing |
| Fresh wheel and source distribution | Passing |
| Five isolated offline wheel examples | Passing |
| Sphinx warnings-as-errors HTML | Passing |
| Wheel-content audit | Passing |

## Comparison with 0.1.0

| Measure | 0.1.0 | 0.2.0 | Change |
|---|---:|---:|---:|
| Wheel | 375,654 B | 390,329 B | +14,675 B (+3.907%) |
| SQLite | 757,760 B | 778,240 B | +20,480 B (+2.703%) |
| Unit tests | 13 | 25 | +12 |
| Doctests | 79 | 157 | +78 |

No local timing regression was detected for import, atlas open, country lookup,
complete iteration, or complete serialization. Named Tokyo-to-Paris lookup and
distance calculation had a 0.299 ms median on the development machine. These
values are regression indicators, not universal performance promises.

## Publication boundary

The package is not yet published. The remaining external sequence is merge and
push, CI across supported Python versions, production PyPI trusted publishing,
GitHub Release publication, and documentation deployment. Borders and border
paths begin in 0.3.0 after 0.2.0 is published.
