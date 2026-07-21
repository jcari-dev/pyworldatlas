Country profiles
================

A :class:`~pyworldatlas.Country` is an immutable, typed view of one country in
the bundled dataset. Autocomplete exposes the current model directly; callers
do not need to remember nested dictionary keys.

A complete current example
--------------------------

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> japan = atlas.country("Japan")
   >>> japan
   Country(name='Japan', alpha2='JP')
   >>> japan.official_name
   'Japan'
   >>> japan.codes.alpha2
   'JP'
   >>> japan.codes.alpha3
   'JPN'
   >>> japan.codes.numeric
   '392'
   >>> japan.continent
   'Asia'
   >>> japan.region
   'Eastern Asia'
   >>> japan.area_km2
   377835.0
   >>> japan.population
   126529100
   >>> (japan.currency.code, japan.currency.name)
   ('JPY', 'Yen')
   >>> japan.calling_codes
   ('+81',)
   >>> japan.top_level_domain
   '.jp'
   >>> [language.code for language in japan.languages]
   ['ja']
   >>> japan.observed_timezones
   ('Asia/Tokyo',)

Names and aliases
-----------------

``country.names`` contains sourced name records with a kind and preferred
marker. ``country.aliases`` is the convenient tuple used for familiar alternate
queries. Common display names may differ from formal UN M49 names while the
formal source value remains available.

Capital and cities
------------------

.. doctest::

   >>> japan.capital
   Capital(name='Tokyo', country_code='JP')
   >>> japan.capital.coordinates.as_tuple()
   (35.6895, 139.69171)
   >>> japan.capital.timezone_id
   'Asia/Tokyo'
   >>> len(japan.major_cities) > 100
   True

Sources
-------

``country.sources`` lists the source snapshots supporting the fields exposed in
the current profile. Core profiles reference UN M49 and GeoNames; countries in
the official-local-name pilot additionally reference UNGEGN.

Immutability
------------

Public models are frozen dataclasses. This prevents one part of an application
from silently changing a shared geographic record. Use :meth:`Country.to_dict
<pyworldatlas.Country.to_dict>` when mutable JSON-compatible data is needed.

.. note::

   Population is a source snapshot rather than a live estimate. Language values
   are source codes, and ``observed_timezones`` contains zones seen on bundled
   capital/major-city records rather than claiming exhaustive legal coverage.
   Government, leaders, historical statistics, and culture remain later work.
