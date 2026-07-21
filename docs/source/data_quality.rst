Data quality and limitations
============================

Validation layers
-----------------

The 0.1.0 build checks:

- Required country identifiers and canonical names.
- Latitude from -90 through 90 and longitude from -180 through 180.
- Non-negative city population values.
- One primary capital for every country in the milestone scope.
- Unique country codes and GeoNames place identifiers.
- Source references for every profile.
- SQLite ``integrity_check`` and foreign-key consistency.
- Reproducible database checksums from identical snapshots.

Coverage
--------

.. list-table:: Current 0.1.0 coverage
   :header-rows: 1
   :widths: 50 25 25

   * - Measure
     - Available
     - Milestone scope
   * - Countries
     - 12
     - 12
   * - Primary capitals
     - 12
     - 12
   * - Capital coordinates
     - 12
     - 12
   * - Major-city records
     - 1,429
     - Population-threshold extract
   * - Country source references
     - 12
     - 12

Missing data is a valid value
-----------------------------

``None`` means the current sources did not provide a field or that its roadmap
milestone has not been implemented. It does not mean zero, false, or an inferred
fact. PyWorldAtlas never fills a gap from model memory.

Interpretation cautions
-----------------------

- Population fields are source snapshots rather than a synchronized census.
- The GeoNames area value is a milestone fallback, not the final area-priority
  implementation.
- Release 0.1.0 selects one GeoNames primary capital per country; nuanced
  multi-capital roles arrive later.
- No boundary geometry, point-in-country, or border claim exists yet.
- Political names and classifications follow documented source conventions and
  do not imply a position on disputed sovereignty.

Run the audit yourself
----------------------

The repository playground validates every exposed record:

.. code-block:: console

   python playground.py --audit-only

