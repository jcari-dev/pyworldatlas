# Builder dependencies

The builder uses only the Python standard library. UN M49 HTML is parsed with
`html.parser`; GeoNames and IANA tab-separated or registry files and ZIP archives
use `csv` and `zipfile`; CLDR XML uses `xml.etree.ElementTree`; reviewed UNGEGN
local-name rows, motto decisions, and English formal-name overrides are read
from CSV. Factbook and Wikidata
snapshots use `json`. Source artifacts are checksummed with `hashlib`,
normalized to JSON Lines, and written to SQLite with `sqlite3`.

`pipeline/scripts/extract_factbook_country_identity.py` is also standard-library
only. It copies structured country-name, anthem-title, and nationality fields
and does not ingest lyrics, contributor credits, adoption history, or profile
narrative text. `pipeline/scripts/extract_cldr_reference_data.py` verifies the
pinned CLDR archive before extracting only the currency and language metadata
used by current profiles.
