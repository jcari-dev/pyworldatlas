# PyWorldAtlas data builder

This is the separate, development-only source ingestion project. It reads
immutable raw snapshots, emits inspectable normalized JSON Lines, validates
them, and builds the one SQLite database shipped by the runtime package.

Run from the repository root:

```console
python maintain.py refresh --offline
```

