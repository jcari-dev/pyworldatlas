PyWorldAtlas 0.1.0
==================

An offline, dependency-free Python atlas generated from sourced data.

Release 0.1.0 contains twelve representative countries. It is useful and
installable, but intentionally does not claim later roadmap features.

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> atlas.country("JP").capital.name
   'Tokyo'
   >>> len(atlas)
   12
   >>> atlas.close()

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   playground
   data_sources
   migration
   api
   _generated/project_status
