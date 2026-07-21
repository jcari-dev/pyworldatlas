# PyWorldAtlas data builder

This is the separate, development-only source ingestion project. It reads
immutable raw snapshots, emits inspectable normalized JSON Lines, validates
them, and builds the one SQLite database shipped by the runtime package.

The current deterministic snapshot generates 248 UN M49 countries and areas,
241 primary capitals, and 6,265 populated-place records. It also builds the
0.2.1 profile fields and five reviewed UNGEGN local names. Missing values remain
missing and are reported rather than synthesized.

Run from the repository root:

```console
python maintain.py refresh --offline
```
