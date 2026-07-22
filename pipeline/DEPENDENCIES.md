# Builder dependencies

The builder uses only the Python standard library. UN M49 HTML is parsed with
`html.parser`; GeoNames tab-separated files and ZIP archives use `csv` and
`zipfile`; CLDR XML uses `xml.etree.ElementTree`; reviewed UNGEGN local-name rows
and English formal-name overrides are read from CSV. Factbook and Wikidata
snapshots use `json`. Source artifacts are checksummed with `hashlib`,
normalized to JSON Lines, and written to SQLite with `sqlite3`.

`pipeline/scripts/extract_factbook_country_identity.py` is also standard-library
only. It copies the structured Factbook `Government > Country name` fields and
does not ingest profile narrative text.
