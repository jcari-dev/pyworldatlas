# Data model

Release 0.1.0 stores normalized country identity, names, capitals, cities,
sources, and per-field provenance in SQLite. Country objects are immutable typed
dataclasses. Multiple capitals are supported by the schema even though this
first fixture release selects one GeoNames primary capital per country. Missing
values remain `None`; profiles are never stored as opaque JSON documents.

