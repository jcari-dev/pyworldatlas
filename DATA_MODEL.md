# Data model

Schema 5 stores normalized countries, names, capitals, populated places, source
references, local identity names, and canonical undirected land-border pairs in
SQLite. Profile columns add population,
currency, language codes, calling codes, country-code top-level domains, and
area. Sourced English formal names use ``country_name`` rows with
``kind = 'formal'`` and field-level provenance. Country, capital, city,
coordinate, currency, language, and source values
are returned as immutable dataclasses.

Schema 5 removes the unused entity-status column. The public model contains
only sourced geographic fields that the package actively uses.

Country discovery features add immutable `CountryReference`, `Flashcard`, and
`CountryDiscoveryCard`, and `BorderPathResult` result models. They are runtime views over existing
profile values and do not add database tables or duplicate source records.

``Country.name`` is the familiar English display identity,
``Country.official_name`` is the canonical UN M49 identity, and
``Country.formal_name`` is the sourced English long form. The last value may
equal the short form and is ``None`` outside the 240-profile source scope.

The schema supports multiple capitals, although the current dataset selects at
most one GeoNames primary capital for each country or area. Exact city lookup
uses the bundled populated-place table. Distance, bearing, and midpoint results
are calculated at runtime from stored WGS84 coordinates and are not persisted.
Flag emoji are derived from alpha-2 codes. Population density is calculated as
snapshot population divided by sourced area. Stable samples and flashcards use
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

Missing scalar values are `None`; missing collections are empty tuples. Country
profiles are normalized records rather than opaque JSON documents. The public
model does not classify entity recognition or legal status. The words
*country* and *area* reflect the documented source scope and are not intended
to provide a broader classification.

`Country.sources` lists the sources that contributed to a profile. It does not
yet provide a value-by-value provenance map. Every local identity carries its
own source reference and locator in `LocalizedName`.
