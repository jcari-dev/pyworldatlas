# Builder dependencies

The normal builder and runtime use only the Python standard library. UN M49 HTML is parsed with
`html.parser`; GeoNames and IANA tab-separated or registry files and ZIP archives
use `csv` and `zipfile`; CLDR XML uses `xml.etree.ElementTree`; reviewed UNGEGN
local-name rows, motto decisions, and English formal-name overrides are read
from CSV. Factbook and Wikidata
snapshots use `json`. Source artifacts are checksummed with `hashlib`,
normalized to JSON Lines, and written to SQLite with `sqlite3`.

`pipeline/scripts/extract_factbook_country_identity.py` is also standard-library
only. It copies the documented country-name, reference, and structured physical
fields and does not ingest lyrics, contributor credits, adoption history,
political narrative, or general profile narrative.
`pipeline/scripts/extract_koppen_country_zones.py` uses Pillow only when a
maintainer deliberately regenerates the compact climate snapshot from the
pinned source raster; Pillow is not a runtime or normal builder dependency.
`pipeline/scripts/extract_cldr_reference_data.py` verifies the
pinned CLDR archive before extracting only the currency and language metadata
used by current profiles.
