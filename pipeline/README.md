# PyWorldAtlas data builder

This is the separate, development-only source ingestion project. It reads
immutable raw snapshots, emits inspectable normalized JSON Lines, validates
them, and builds the one SQLite database shipped by the runtime package.

The current deterministic snapshot generates 248 UN M49 countries and areas,
241 primary capitals, 6,265 populated-place records, rich profile fields, one
CLDR/UNGEGN local identity per country or area, 10 selected reviewed UNGEGN
official short/formal records, 240 sourced English formal names, and the
reviewed land-border graph. Version 0.6 also generates 234 anthem-title
profiles, 32 reviewed mottos, 227 demonym profiles, 722 country-language
records, 417 timezone records, and practical currency/postal metadata. Missing
values remain missing and are reported rather than synthesized.

Run from the repository root:

```console
python maintain.py refresh --offline
```
