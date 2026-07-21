Official local names
====================

The 0.2.0 Country Discovery work begins with official short and formal country
names in languages used by the country itself. These records are bundled in the
SQLite dataset, remain available after an :class:`~pyworldatlas.Atlas` closes,
and never require a network request.

The first reviewed vertical slice covers Brazil and Switzerland. Countries not
yet covered return an empty tuple and the convenience methods return ``None``.
There is deliberately no English fallback and no generated romanization.

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> brazil = atlas.country("Brazil")
   >>> brazil.name_in("pt")
   'Brasil'
   >>> brazil.official_name_in("pt")
   'República Federativa do Brasil'
   >>> brazil.name_in("en") is None
   True
   >>> brazil.romanized_name_in("pt") is None
   True
   >>> swiss = atlas.country("Switzerland")
   >>> [(name.language_code, name.short_name) for name in swiss.local_names]
   [('de', 'Schweiz'), ('fr', 'Suisse'), ('it', 'Svizzera'), ('rm', 'Svizra')]
   >>> atlas.close()
   >>> swiss.official_name_in("rm")
   'Confederaziun svizra'

Each :class:`~pyworldatlas.LocalizedName` includes a language code and display
name, ISO 15924 script code, short and formal forms, explicit romanization
fields, an official-language flag, and a :class:`~pyworldatlas.SourceReference`.

Source policy
-------------

The pilot is a reviewed transcription of the UNGEGN Working Group on Country
Names document ``E/CONF.105/13/CRP.13`` dated 17 July 2017. The exact PDF is
captured with a SHA-256 manifest, and every reviewed row carries an entry and
page locator.

Coverage boundary
-----------------

This is intentionally a two-country pilot. It proves the source-to-wheel path,
Unicode handling, provenance, serialization, lifecycle behavior, and bounded
query strategy before expanding coverage. Empty results for other countries
mean “not yet covered by this data family,” not “the country has no local name.”
