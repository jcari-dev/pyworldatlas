# Data model

Schema 3 stores normalized countries, names, capitals, populated places, source
references, official local names, and canonical undirected land-border pairs in
SQLite. Profile columns add population,
currency, language codes, calling codes, country-code top-level domains, and
area. Country, capital, city, coordinate, currency, language, and source values
are returned as immutable dataclasses.

Country discovery features add immutable `CountryReference`, `Flashcard`, and
`CountryDiscoveryCard`, and `BorderPathResult` result models. They are runtime views over existing
profile values and do not add database tables or duplicate source records.

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

Missing scalar values are `None`; missing collections are empty tuples. Country
profiles are normalized records rather than opaque JSON documents. The current
dataset does not include a sourced political-entity classification, so
`Country.status` is `CountryStatus.OTHER` for every record.

`Country.sources` lists the sources that contributed to a profile. It does not
yet provide a value-by-value provenance map. Reviewed official local names carry
their own source reference in `LocalizedName.source`.
