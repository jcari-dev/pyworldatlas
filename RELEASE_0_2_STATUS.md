# PyWorldAtlas 0.2.0 release status

Version 0.2.0 turns the stable 0.1.0 world core into a useful rich-profile and
coordinate release. It keeps the standard-library-only runtime, bundled SQLite
database, deterministic builder, immutable models, and offline behavior.

## Implemented scope

| Capability | State |
|---|---|
| 248 country and area profiles | Complete |
| Population snapshot | Complete |
| Currency code and name | Complete |
| Language codes | Complete |
| International calling codes | Complete |
| Country-code top-level domain | Complete |
| Observed capital/major-city timezones | Complete |
| Primary-capital coordinates | Complete |
| Exact city lookup with ambiguity protection | Complete |
| Validated latitude/longitude objects | Complete |
| Great-circle kilometres, miles, and nautical miles | Complete |
| Initial bearing | Complete |
| Spherical midpoint | Complete |
| Named-place and raw-coordinate distance helpers | Complete |
| Brazil/Switzerland official-local-name pilot | Complete |
| Borders and border paths | Reserved for 0.3.0 |

## Public examples

```python
from pyworldatlas import Atlas, Coordinate

with Atlas() as atlas:
    japan = atlas.country("Japan")
    print(japan.population)
    print(japan.currency)
    print(japan.languages)
    print(japan.calling_codes)
    print(japan.capital_coordinates)

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
- Language values are source language codes rather than invented display names.
- Country distance uses primary-capital coordinates and is documented as
  capital-to-capital distance, not centroid distance.
- Named city lookup never silently chooses between multiple exact matches.
- Great-circle distance is a spherical surface calculation, not a road or
  flight-routing result.
- Official local names retain the narrow, visually verified two-country pilot.

## Release gate

Before publishing 0.2.0:

- Run supported-Python CI.
- Confirm deterministic database rebuilds.
- Pass the complete unit-test and playground audit.
- Build Sphinx with warnings as errors and pass every doctest.
- Build one wheel and one source distribution.
- Install and run examples from the isolated offline wheel.
- Audit wheel contents and compare wheel/database size with 0.1.0.
- Create release checksums and the machine-readable release manifest.
- Smoke-test installation from TestPyPI before production PyPI.
- Publish the GitHub Release and deploy the updated documentation only after
  those checks pass.

## Next release

Version 0.3.0 will add reviewed border relationships, neighbors, shared
neighbors, deterministic shortest border paths, dispute-policy documentation,
and graph-level validation. It will not infer borders from the unreviewed
GeoNames neighbor column.

## Environment note

The repository's current `.venv` launcher points to a removed Python 3.10
installation. Recreate the environment from an installed Python interpreter in
VS Code before release testing. This environment issue is independent of the
package and does not affect the passing maintained Python runtime.
