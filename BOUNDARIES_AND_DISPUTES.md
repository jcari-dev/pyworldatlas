# Land-border data scope

PyWorldAtlas provides land-border relationships for geographic learning. The
graph records a reproducible convention from documented source snapshots. It
does not provide political commentary or decide geographic disagreements.

Version 0.3.0 contains a reviewed graph of land-border relationships. It does
not contain boundary geometry, border lengths, maritime boundaries,
point-in-country operations, or route data.

The automatic review baseline is the intersection of the captured GeoNames
neighbor field and shared polygon segments in Natural Earth 1:50m map units.
The snapshots agree on 315 relationships. Every one of their six differences
has an explicit decision in `build_data/reviewed/border_decisions.csv`: four
relationships are included and two are excluded. The final graph contains 319
canonical undirected relationships.

UN M49 supplies the package identity scope. Natural Earth and GeoNames can use
different names, entity splits, or levels of detail. The builder applies
documented mappings and review decisions only to create consistent join keys
and a reproducible graph. No broader interpretation should be drawn from those
technical mappings.

No single source convention covers every use case. The project therefore
states its scope, attributes its sources, and records every exceptional decision
in `build_data/reviewed/border_decisions.csv`. Corrections are evaluated against
the declared source and topology rules.

Country distance remains capital-to-capital distance and must not be interpreted
as a boundary or centroid measurement. Geometry and point-in-boundary work begin
in 0.7.0 and require a separate documented source and precision review.

The governing educational and editorial principles are recorded in
`EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.
