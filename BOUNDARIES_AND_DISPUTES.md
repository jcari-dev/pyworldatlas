# Boundaries and disputes

Version 0.3.0 contains a reviewed graph of land-border relationships. It does
not contain boundary geometry, border lengths, maritime boundaries,
point-in-country operations, or route data.

The automatic review baseline is the intersection of the captured GeoNames
neighbor field and shared polygon segments in Natural Earth 1:50m map units.
The snapshots agree on 315 relationships. Every one of their six differences
has an explicit decision in `build_data/reviewed/border_decisions.csv`: four
relationships are included and two are excluded. The final graph contains 319
canonical undirected relationships.

UN M49 supplies the 248-country-and-area package scope. Natural Earth's map
units use its documented de facto worldview. Kosovo is not a separate entity in
the current UN M49 scope, but its Natural Earth geometry is not reassigned to a
neighboring country; Albania and Serbia therefore do not receive a direct edge.
Somaliland and Northern Cyprus geometry is associated with the corresponding
UN-scope Somalia and Cyprus entities for topology extraction. These data-model
choices do not express a position on sovereignty or recognition.

Small territories and enclaves can disappear as shared polygon segments at
1:50m. Gibraltar–Spain and Morocco–Spain are retained through explicit reviewed
decisions based on the captured GeoNames relationships. China–Hong Kong and
China–Macao are retained from Natural Earth map-unit topology. United
States–Cuba is excluded because it is not a land border.

Country distance remains capital-to-capital distance and must not be interpreted
as a boundary or centroid measurement. Geometry and point-in-boundary work begin
in 0.4.0 and will require a separate documented worldview policy.
