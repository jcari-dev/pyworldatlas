# Data model reference

Schema 7 stores normalized countries, names, capitals, populated places, source
references, local identity names, and canonical undirected land-border pairs in
SQLite. Profile columns add population,
currency, language codes, calling codes, country-code top-level domains, and
area. Structured physical facts use `country_physical`, `country_river`,
`country_lake`, and `country_climate_zone` rows. Sourced English formal names
use `country_name` rows with `kind = 'formal'` and field-level provenance.
Public country, place, reference, and physical values are immutable dataclasses.

The public model contains only sourced geographic fields that the package
actively uses.

Country discovery features add immutable `CountryReference`, `Flashcard`, and
`CountryDiscoveryCard`, and `BorderPathResult` result models. They are runtime views over existing
profile values and do not add database tables or duplicate source records.

Physical geography adds immutable `ElevationPoint`, `River`, `Lake`,
`ClimateZone`, `ClimateProfile`, and `PhysicalGeography` models. Area components
remain grouped under `Geography.area`; the other physical values are grouped
under `Geography.physical` and exposed through `Country` conveniences.

``Country.name`` is the familiar English display identity,
``Country.official_name`` is the canonical UN M49 identity, and
``Country.formal_name`` is the sourced English long form. The last value may
equal the short form and is ``None`` outside the 240-profile source scope.

The schema supports multiple capitals, although the current dataset selects at
most one GeoNames primary capital for each country or area. Exact city lookup
uses the bundled populated-place table. Distance, bearing, and midpoint results
are calculated at runtime from stored WGS84 coordinates and are not persisted.
Flag emoji are derived from alpha-2 codes. Population density is calculated as
snapshot population divided by sourced total area; water percentage is water
area divided by total area. Stable samples and flashcards use
a versioned SHA-256 ranking over M49 identifiers; they never mutate profiles or
store lesson state.

Each `country_border` row stores the two country identifiers in canonical order,
its review status, its evidence-source identifiers, and an optional decision
note. Runtime adjacency is symmetric. Shortest paths use breadth-first search
and are calculated on demand; paths and connected components are not persisted.
`BorderPathResult.names` and `alpha2_codes` are projections of its immutable
country references. Land-route checks and border flashcards are derived from
the same graph and do not create additional tables or country facts.

Each `country_local_name` row represents the selected local identity for one
country or area. `name_kind` distinguishes a CLDR `locale_display` value from a
reviewed UNGEGN `national_official` form, and `language_status` records how the
language was selected. The public `LocalizedName` preserves these fields,
language and script identifiers, any sourced formal form or romanization,
source reference, and exact locator. Country convenience methods only project
these records; they never translate or generate a fallback.

Each `country_physical` row holds optional area components, coastline, mean
elevation, named highest/lowest points, a plain-language climate summary, and
direct source provenance. River and lake child rows are source-listed major
features, not exhaustive inventories. Climate-zone child rows contain one
represented Köppen-Geiger class and its latitude-area-weighted share. The
reference period, source resolution, and extraction threshold are retained in
the physical row.

Missing scalar values are `None`; missing collections are empty tuples. Country
profiles are normalized records rather than opaque JSON documents. The public
model does not classify entity recognition or legal status. The words
*country* and *area* reflect the documented source scope and are not intended
to provide a broader classification.

`Country.sources` lists the sources that contributed to a profile. Direct
provenance is available on local identity, reference-fact, physical, and climate
models. Other core fields still use the profile-level source summary.
