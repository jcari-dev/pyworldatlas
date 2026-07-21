# PyWorldAtlas 0.2.0 release status

Version 0.2.0 adds country profile metadata, coordinate tools, and reproducible
country-discovery features to the 0.1.0 world core. It keeps the
standard-library-only runtime, bundled SQLite database, deterministic builder,
immutable models, and offline behavior.

## Implemented scope

| Capability | Coverage or state |
|---|---|
| Country and area profiles | 248 |
| Population snapshots | 248 / 248 |
| Currency code and name | 247 / 248 |
| Language-code collections | 245 / 248 |
| International calling codes | 243 / 248 |
| Country-code top-level domains | 248 / 248 |
| Profiles with observed timezones | 242 / 248 |
| Primary-capital coordinates | 241 / 248 |
| Exact city lookup with ambiguity protection | 6,265 bundled places |
| Validated latitude/longitude objects | Implemented |
| Great-circle kilometres, miles, and nautical miles | Implemented |
| Initial bearing and spherical midpoint | Implemented with undefined-case errors |
| Named-place, model, and raw-coordinate distance inputs | Implemented |
| Flag emoji derived from alpha-2 codes | 248 / 248 |
| Calculated population density | Available when population and area are usable |
| Immutable discovery cards and country references | Implemented |
| Deterministic filtered country sampling | Implemented |
| Structured educational flashcards | 16 documented topics |
| Official local names | 5 records across Brazil and Switzerland |
| Borders and border paths | Reserved for 0.3.0 |

## Usage example

```python
from pyworldatlas import Atlas, Coordinate

with Atlas() as atlas:
    japan = atlas.country("Japan")
    print(japan.population)
    print(japan.currency)
    print(japan.languages)
    print(japan.calling_codes)
    print(japan.capital_coordinates)
    print(japan.flag_emoji)
    print(japan.population_density)
    print(japan.discovery_card().to_dict())

    print(atlas.sample_countries(count=5, continent="Africa", seed=42))
    print(atlas.flashcards(topic="capitals", count=3, seed=42))

    tokyo = atlas.city("Tokyo", country="JP")
    paris = atlas.city("Paris", country="FR")
    print(atlas.distance_between(tokyo, paris))
    print(tokyo.coordinates.bearing_to(paris.coordinates))
    print(tokyo.coordinates.midpoint_to(paris.coordinates))

print(Coordinate(51.5074, -0.1278).distance_to(Coordinate(48.8566, 2.3522)))
```

## Data semantics

- Population and currency values are snapshots from the captured GeoNames
  country metadata; they are not live economic data.
- `observed_timezones` is derived from bundled capital and major-city rows and
  is not presented as an exhaustive legal timezone list.
- Language values are source codes; display names are not included.
- Country distance uses primary-capital coordinates and is documented as
  capital-to-capital distance, not centroid distance.
- Named city lookup raises an ambiguity error when multiple exact matches exist.
- Great-circle distance is a spherical surface calculation, not a road or
  flight-routing result.
- Official local names retain the narrow, visually verified two-country pilot.
- Flag emoji, density, discovery cards, samples, and flashcards are derived from
  existing sourced profile values and introduce no new country-data authority.

## Local release checks

The current checkout passes deterministic database rebuilds, 25 unit tests, the
complete playground audit, Sphinx warnings-as-errors, 157 doctests, five
isolated wheel examples, and the wheel-content audit. The release build also writes
SHA-256 checksums and a machine-readable manifest.

## External publication checks

Before production publication:

- Confirm supported-Python CI on the release commit.
- Install and smoke-test 0.2.0 from TestPyPI in a clean environment.
- Verify the protected `pypi` environment and trusted publisher.
- Push `v0.2.0` only after the TestPyPI package matches the local artifact.
- Verify the PyPI page, GitHub Release assets, and deployed documentation.

## Next release

Version 0.3.0 will add reviewed border relationships, neighbors, shared
neighbors, deterministic shortest border paths, dispute-policy documentation,
and graph-level validation. It will not infer borders from the unreviewed
GeoNames neighbor column.
