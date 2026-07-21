Capitals and major cities
=========================

Capital records
---------------

Every country in the 0.1.0 scope has one primary capital sourced from GeoNames.
The schema supports multiple capitals so later releases can represent
administrative, legislative, judicial, and other roles without redesigning the
runtime model.

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> capital = atlas.country("Dominican Republic").capital
   >>> capital.name
   'Santo Domingo'
   >>> capital.coordinates.as_tuple()
   (18.47186, -69.89232)
   >>> capital.role
   'official'
   >>> capital.primary
   True

Coordinates are signed WGS84 decimal degrees. Positive latitude is north;
positive longitude is east.

Major cities
------------

Release 0.1.0 retains populated places at or above the configured 100,000-person
threshold and always retains capitals. Results are ordered by population, then
name.

.. doctest::

   >>> cities = atlas.major_cities("Japan", limit=3)
   >>> [city.name for city in cities]
   ['Tokyo', 'Yokohama', 'Osaka']
   >>> cities[0].geonames_id
   1850147
   >>> atlas.close()

Population values describe the captured source snapshot. They are not live
estimates and should not be interpreted as a synchronized census series.

