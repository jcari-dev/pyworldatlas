Serialization
=============

Country models serialize to JSON-compatible primitives without exposing SQLite
rows or implementation details.

Dictionary output
-----------------

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> with Atlas() as atlas:
   ...     data = atlas.country("DO").to_dict()
   >>> data["codes"]["alpha2"]
   'DO'
   >>> data["capitals"][0]["name"]
   'Santo Domingo'

JSON output
-----------

.. doctest::

   >>> import json
   >>> with Atlas() as atlas:
   ...     payload = atlas.country("JP").to_json()
   >>> json.loads(payload)["name"]
   'Japan'

Tuples become JSON arrays and enums become their string values.
``include_history`` is accepted for compatibility but currently has no effect
because historical series are not bundled.
