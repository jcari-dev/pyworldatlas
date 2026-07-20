# Data sources

## United Nations M49

- Purpose: canonical country/area names, ISO and M49 codes, regions, subregions.
- Official URL: https://unstats.un.org/unsd/methodology/m49/
- Snapshot: captured 2026-07-20 as raw HTML with SHA-256 manifest.
- License/terms: United Nations website terms apply.
- Refresh cadence: monthly review.
- Weaknesses: formal names are not always the most familiar English atlas names.

## GeoNames

- Purpose: capitals, coordinates, major cities, alternate names, area cross-check.
- Official URL: https://download.geonames.org/export/dump/
- Snapshot: `countryInfo.txt` and `cities15000.zip`, captured 2026-07-20 with SHA-256 manifests.
- License: Creative Commons Attribution 4.0.
- Refresh cadence: weekly review, monthly release as appropriate.
- Weaknesses: capital feature codes do not model every multi-capital political nuance.

