# Builder dependencies

The builder uses only the Python standard library. UN M49 HTML is parsed with
`html.parser`; GeoNames tab-separated files and ZIP archives use `csv` and
`zipfile`; reviewed UNGEGN local-name rows are read from CSV. Source artifacts
are checksummed with `hashlib`, normalized to JSON Lines, and written to SQLite
with `sqlite3`.
