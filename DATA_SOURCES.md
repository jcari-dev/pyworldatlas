# Data sources

## United Nations M49

- Purpose: canonical country/area names, ISO and M49 codes, regions, subregions.
- Official URL: https://unstats.un.org/unsd/methodology/m49/
- Snapshot: captured 2026-07-20 as raw HTML with SHA-256 manifest.
- License/terms: United Nations website terms apply.
- Refresh: reviewed before each dataset release.
- Limitations: formal names are not always the most familiar English atlas names.

The current source-priority scope contains 248 UN M49 countries and areas.
GeoNames-only identity rows outside that scope are excluded rather than inferred.

## GeoNames

- Purpose: capitals, coordinates, major cities, country population snapshots,
  currencies, language codes, calling codes, top-level domains, alternate names,
  and area cross-check.
- Official URL: https://download.geonames.org/export/dump/
- Snapshot: `countryInfo.txt` and `cities15000.zip`, captured 2026-07-20 with SHA-256 manifests.
- License: Creative Commons Attribution 4.0.
- Refresh: reviewed before each dataset release.
- Limitations: capital feature codes do not model every multi-capital political nuance.

The captured intersection provides 241 usable primary-capital records and 6,265
populated-place records: places at or above the configured 100,000-person
threshold, plus retained capitals.

## UNGEGN List of Country Names

- Purpose: national official short and formal country names and languages.
- Official URL: https://unstats.un.org/unsd/ungegn/working_groups/wg1.cshtml
- Snapshot: `E/CONF.105/13/CRP.13`, dated 2017-07-17, captured as an exact PDF
  with a SHA-256 manifest.
- Review layer: `build_data/reviewed/country_local_names.csv`, with exact entry
  and page locators for every row.
- Current scope: five records across Brazil and Switzerland.
- Limitations: the five reviewed records do not imply full-world local-name
  coverage.
