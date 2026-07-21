Lookup, search, and filtering
=============================

Exact lookup
------------

:meth:`Atlas.country <pyworldatlas.Atlas.country>` accepts common names,
aliases, ISO alpha-2 and alpha-3 identifiers, and M49 numeric codes. Lookup is
case- and accent-insensitive.

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> atlas.country("usa").name
   'United States'
   >>> atlas.country("VAT").name
   'Vatican City'

Safe lookup
-----------

Use :meth:`Atlas.get <pyworldatlas.Atlas.get>` when a missing query is an
ordinary possibility:

.. doctest::

   >>> atlas.get("Atlantis") is None
   True

Ranked search
-------------

.. doctest::

   >>> matches = atlas.search_countries("united")
   >>> [(match.country.name, match.score) for match in matches]
   [('United States', 80)]

Filtering
---------

.. doctest::

   >>> [country.name for country in atlas.countries(continent="Americas")]
   ['Bolivia', 'Brazil', 'Canada', 'Cuba', 'Dominican Republic', 'United States']
   >>> [country.name for country in atlas.countries(region="Caribbean")]
   ['Cuba', 'Dominican Republic']
   >>> atlas.close()

