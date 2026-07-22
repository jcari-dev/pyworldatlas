# Data sources

## Field-specific source policy

Each source is selected for a specific field. The project prefers established
standards bodies, international statistical and naming publications, openly
licensed geographic datasets, and primary institutional records when they are
appropriate for that field. Commentary, anonymous compilations, unsupported
claims, and advocacy material are not used as dataset authorities.

No source is presented as universally neutral or complete. A source may reflect
a particular date or naming convention. PyWorldAtlas records those limitations,
uses independent cross-checks where useful, and publishes review decisions.
Including a source value is not an endorsement of the source organization or a
broader interpretation. See `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.

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
  postal-code formats, timezone records, and area cross-check.
- Official URL: https://download.geonames.org/export/dump/
- Snapshot: `countryInfo.txt` and `cities15000.zip`, captured 2026-07-20;
  `timeZones.txt`, captured 2026-07-22; all have SHA-256 manifests.
- License: Creative Commons Attribution 4.0.
- Refresh: reviewed before each dataset release.
- Limitations: capital feature codes do not model every multi-capital arrangement.

The captured intersection provides 241 usable primary-capital records and 6,265
populated-place records: places at or above the configured 100,000-person
threshold, plus retained capitals.

The timezone table contributes 417 records across 246 profiles. GeoNames also
provides postal-code display formats for 176 profiles.

## UNGEGN List of Country Names

- Purpose: national official short and formal country names and languages.
- Official URL: https://unstats.un.org/unsd/ungegn/working_groups/wg1.cshtml
- Snapshot: `E/CONF.105/13/CRP.13`, dated 2017-07-17, captured as an exact PDF
  with a SHA-256 manifest.
- Review layer: `build_data/reviewed/country_local_names.csv`, with exact entry
  and page locators for every row.
- Current development scope: 10 selected records with reviewed national short
  and formal names. This batch is not complete local national-official
  coverage.
- Limitations: UNGEGN covers independent states rather than every area in the
  248-record UN M49 runtime scope.

## Unicode CLDR 48.2

- Purpose: localized territory display names, currency names/symbols/minor
  units, language names, and likely scripts.
- Official URL: https://unicode.org/Public/cldr/48.2/
- Snapshot: a compact 248-row extraction from `cldr-common-48.2.zip`, retaining
  the archive URL/checksum and exact locale/XPath locators.
- Extractors: `pipeline/scripts/extract_cldr_country_identity.py` and
  `pipeline/scripts/extract_cldr_reference_data.py`.
- License: Unicode License v3.
- Coverage: 248 / 248 local display names across 80 languages and 21 scripts;
  244 selections use an official, de-facto official, or regional official
  language.
- Limitations: CLDR territory labels are localized display names. They are not
  automatically diplomatic formal names, and the API labels them accordingly.

## IANA Language Subtag Registry

- Purpose: English language-name fallback for captured codes not labelled by CLDR.
- Official URL: https://www.iana.org/assignments/language-subtag-registry/
- Snapshot: registry dated 2026-06-14, captured 2026-07-22 with SHA-256 manifest.
- Terms: protocol registry data is provided under the IANA/IETF CC0 1.0
  licensing statement at https://www.iana.org/help/licensing-terms.
- Use: description fallback only; no official-language status is inferred.

## CIA World Factbook structured profiles

- Purpose: base English formal-name layer, anthem titles, English demonyms,
  area components, coastline, mean elevation, highest/lowest points,
  source-listed major rivers/lakes, and short climate descriptions.
- Official URL: https://www.cia.gov/the-world-factbook/
- Structured snapshot: `factbook.json` commit
  `8662a8b17a784841ab4528631b04090eb2f183eb`, reduced deterministically to the
  documented identity, reference, and structured physical-geography fields.
- Extractor: `pipeline/scripts/extract_factbook_country_identity.py`.
- Terms: public domain under the CIA site policy and the structured
  repository's public-domain dedication.
- Coverage: 195 distinct long forms and 45 profiles where the source supplies
  no distinct long form, 234 anthem-title profiles, and 227 demonym profiles.
- Limitations: AX, BQ, GF, GP, MQ, RE, UM, and YT are outside the captured
  source intersection and remain `None`.
- Physical coverage: 238 total/land-area and coastline profiles, 233 numeric
  water-area profiles, 240 highest/lowest-point and climate-summary profiles,
  166 mean-elevation profiles, 188 river records across 80 profiles, and 187
  lake records across 69 profiles.
- Exclusions: lyrics, audio, contributor credits, adoption histories,
  political narrative, and general profile narrative are not extracted.

## Köppen-Geiger climate classification maps

- Purpose: broad physical-climate classification for country and area profiles.
- Publication: https://doi.org/10.1038/s41597-023-02549-6
- Data: https://doi.org/10.6084/m9.figshare.21937571.v1
- Snapshot: 0.1-degree 1991–2020 historical raster and 30-class legend,
  Beck et al. dataset version 1, with pinned source and derived checksums.
- License: the Figshare data release is CC0 1.0.
- Derivation: raster cell centres are matched to pinned Natural Earth 1:50m
  map units, weighted by latitude, grouped by runtime profile, and filtered at
  a minimum represented share of 0.1%.
- Coverage: 241 / 248 profiles. BV, GI, MH, MV, TK, TV, and UM have no
  represented cells after the documented intersection rules.
- Limitations: shares are generalized broad-scale estimates, not local
  forecasts, property-boundary results, or site-level classifications.

## Wikidata national-motto statements

- Purpose: reviewed source-listed national motto labels.
- Query endpoint: https://query.wikidata.org/sparql
- Snapshot: 2026-07-22, with exact query, response checksum, statement IDs,
  ranks, and multilingual labels retained.
- License: Creative Commons CC0 1.0.
- Review: every captured item-valued statement has an explicit decision in
  `build_data/reviewed/national_motto_decisions.csv`.
- Coverage: 32 included profiles.
- Limitation: the package does not infer legal status and excludes unreviewed,
  conflicting, historical, imprecisely labelled, or duplicate statements.

## United Nations Protocol and Liaison Service

- Purpose: five current English formal-name excerpts used where the final
  Factbook snapshot differs from current UN usage.
- Official document: *Official Names of the United Nations Membership*, dated
  2025-02-05.
- URL: https://www.un.org/dgacm/sites/www.un.org.dgacm/files/Documents_Protocol/officialnamesofcountries.pdf
- Use: exact entries for Afghanistan, Italy, Niger, Türkiye, and Viet Nam,
  each with a PDF page locator in the reviewed override file.
- Retention: the PDF checksum and metadata are recorded, but the PDF is not
  redistributed in this repository.
- Review-only check: a current UNTERM country-name export was inspected to
  compare the 193 UN-member entries. It is not redistributed and no package
  record is sourced from that workbook.

## Wikidata official-name statements

- Purpose: three reviewed English formal-name corrections where exact current
  statements are available under CC0.
- Query endpoint: https://query.wikidata.org/sparql
- Snapshot: 2026-07-21, with the exact query, result checksum, statement IDs,
  ranks, and qualifiers retained.
- License: Creative Commons CC0 1.0.
- Use: Guyana, Saint Kitts and Nevis, and Myanmar only.
- Limitation: Wikidata is not used as an unreviewed bulk authority; every used
  statement is pinned by ID and value.

## Natural Earth

- Purpose: independent land-border topology from shared segments in the 1:50m
  Admin 0 map-unit polygons, plus build-time aggregation of climate raster
  cells into country profiles.
- Official URL: https://www.naturalearthdata.com/downloads/50m-cultural-vectors/
- Snapshot: boundary lines 5.1.0 and country/map-unit archives 5.1.1, captured
  2026-07-21 with SHA-256 manifests.
- Terms: public domain; personal, educational, and commercial use is permitted.
- Review role: cross-check GeoNames neighbor records. The 315 agreements are
  accepted automatically, while every source difference requires a recorded
  decision in `build_data/reviewed/border_decisions.csv`.
- Limitations: generalized 1:50m geometry may omit shared segments for small
  territories and enclaves, and Natural Earth applies a documented de facto
  map convention. The polygons are not exposed as public boundary geometry in
  0.7.

The reviewed 0.3.0 graph contains 319 canonical undirected relationships: 315
cross-source agreements and four explicit inclusions. Two source-only
relationships are explicitly excluded.

## Derived discovery values

Flag emoji are calculated from the UN/ISO alpha-2 code. Population density is
the captured GeoNames population divided by the sourced total-area value;
water percentage is water area divided by total area. Discovery
cards, deterministic samples, and flashcards only select, arrange, or calculate
from already attributed profile fields; they add no external country facts.

Country rankings sort documented fields or transparent derived counts/ratios.
Nearest-capital results use the package's great-circle distance calculation.
These are exploration tools, not evaluations of countries or people.

The sampling algorithm ranks M49 identifiers with SHA-256 and never calls a
remote service. Flashcard wording is package code under the project license;
answers retain the provenance and freshness limits of their underlying fields.
Neighbor and border-count flashcards are calculated from the reviewed 0.3.0
graph and introduce no additional border claims.

Physical rankings and flashcards reuse the documented physical fields. River
and lake counts describe source-listed records rather than exhaustive
inventories. Köppen-Geiger classes reuse the pinned derived country snapshot.
