# Data model

Schema 2 stores normalized countries, names, capitals, populated places, source
references, and official local names in SQLite. Profile columns add population,
currency, language codes, calling codes, country-code top-level domains, and
area. Country, capital, city, coordinate, currency, language, and source values
are returned as immutable dataclasses.

Country discovery features add immutable `CountryReference`, `Flashcard`, and
`CountryDiscoveryCard` result models. They are runtime views over existing
profile values and do not add database tables or duplicate source records.

The schema supports multiple capitals, although the current dataset selects at
most one GeoNames primary capital for each country or area. Exact city lookup
uses the bundled populated-place table. Distance, bearing, and midpoint results
are calculated at runtime from stored WGS84 coordinates and are not persisted.
Flag emoji are derived from alpha-2 codes. Population density is calculated as
snapshot population divided by sourced area. Stable samples and flashcards use
a versioned SHA-256 ranking over M49 identifiers; they never mutate profiles or
store lesson state.

Missing scalar values are `None`; missing collections are empty tuples. Country
profiles are normalized records rather than opaque JSON documents. The current
dataset does not include a sourced political-entity classification, so
`Country.status` is `CountryStatus.OTHER` for every record.

`Country.sources` lists the sources that contributed to a profile. It does not
yet provide a value-by-value provenance map. Reviewed official local names carry
their own source reference in `LocalizedName.source`.
