# Migrating from 0.0.x

The 0.1.0 release is an intentional clean break. Construct `Atlas()` and request
immutable `Country` objects with `atlas.country("Japan")` or `atlas["JP"]`.
Legacy dictionaries, legacy coordinate fields, and the old database schema are
not retained.

