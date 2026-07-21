# PyWorldAtlas

PyWorldAtlas is a compact, dependency-free Python atlas that works entirely
offline. Release 0.1.0 is the first clean rebuild: it contains twelve
representative countries generated from captured UN M49 and GeoNames sources,
with names, standard codes, regions, capitals, coordinates, and major cities.

```console
pip install pyworldatlas
```

```python
from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")
    print(japan.capital.name)             # Tokyo
    print(japan.capital.coordinates)      # signed WGS84 decimal degrees
    print(atlas["DO"].name)               # Dominican Republic
```

The runtime makes no network requests, writes no files during import, and uses
only the Python standard library plus one bundled SQLite database. Library
version `0.1.0`, schema version `1`, and dataset version `2026.07.20` are
independent and available from `atlas.dataset_info()`.

Current scope: 12 countries and 12 primary capitals. Later roadmap features are
not claimed as implemented. See the [public documentation](https://jcari-dev.github.io/pyworldatlas-documentation/)
and `ROADMAP_STATUS.md` for precise status.

Data sources: UN M49 for canonical identities/regions and GeoNames (CC BY 4.0)
for populated places. See `DATA_SOURCES.md` and `THIRD_PARTY_NOTICES.md`.

## VS Code playground

Open this repository in VS Code, select the project virtual environment, and
press `F5`. Choose **PyWorldAtlas: Full Playground** to validate every current
country, capital, and major-city record and then see every implemented API
feature in action. The repository playground runs directly from ``src/`` when
the package has not yet been installed. Focused terminal modes are also available:

```console
python playground.py --audit-only
python playground.py --country Japan
python playground.py --json "Dominican Republic"
python playground.py --country "United States" --all-cities
```

The `0.x` runtime targets Python 3.10 through 3.14. Documentation setup selects
Sphinx 8.1.3 on Python 3.10 and Sphinx 8.2.3 on newer Python versions; this keeps
the developer setup compatible without adding any runtime dependency.
