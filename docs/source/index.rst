PyWorldAtlas
============

.. raw:: html

   <section class="atlas-hero">
     <div class="atlas-eyebrow">Offline geography for Python</div>
     <h1>Keep the world close.</h1>
     <p>A small, source-aware atlas for learning, teaching, prototyping, and exploring—without API keys, runtime downloads, or third-party dependencies.</p>
     <div class="atlas-badges">
       <span class="atlas-badge">Release 0.1.0</span>
       <span class="atlas-badge">Dataset 2026.07.20</span>
       <span class="atlas-badge">Python 3.10–3.14</span>
       <span class="atlas-badge">100% offline runtime</span>
     </div>
   </section>

.. raw:: html

   <div class="atlas-stats">
     <div class="atlas-stat"><strong>12</strong><span>representative countries</span></div>
     <div class="atlas-stat"><strong>12</strong><span>primary capitals</span></div>
     <div class="atlas-stat"><strong>1,429</strong><span>major-city records</span></div>
     <div class="atlas-stat"><strong>0</strong><span>runtime dependencies</span></div>
   </div>

Two lines to the atlas
----------------------

.. doctest::

   >>> from pyworldatlas import Atlas
   >>> atlas = Atlas()
   >>> japan = atlas.country("Japan")
   >>> japan.capital.name
   'Tokyo'
   >>> japan.capital.coordinates.as_tuple()
   (35.6895, 139.69171)
   >>> atlas.close()

The installed wheel contains ordinary Python source and one read-only SQLite
database. Constructing :class:`~pyworldatlas.Atlas` never contacts a server and
does not load the complete dataset into memory.

.. raw:: html

   <div class="atlas-note"><strong>An honest first release.</strong> Version 0.1.0 proves the new architecture with twelve representative countries. It does not pretend to be the final full-world dataset. Every page clearly distinguishes what works today from what arrives in later milestones.</div>

Designed to be explored
-----------------------

.. raw:: html

   <div class="atlas-cards">
     <article class="atlas-card"><h3>Start in sixty seconds</h3><p>Install the package, look up a country, and inspect its capital and identifiers.</p><a href="quickstart.html">Read the quickstart →</a></article>
     <article class="atlas-card"><h3>See the complete profile</h3><p>Understand every field available in the current immutable country model.</p><a href="country_profile.html">Tour a country profile →</a></article>
     <article class="atlas-card"><h3>Test every record</h3><p>Run the VS Code playground to audit all countries, capitals, and cities.</p><a href="playground.html">Open the playground guide →</a></article>
     <article class="atlas-card"><h3>Trust the data trail</h3><p>See exactly which source provides identity, regions, capitals, and cities.</p><a href="data_sources.html">Inspect sources and quality →</a></article>
   </div>

What works in 0.1.0
-------------------

- Exact lookup by common name, alias, ISO alpha-2, ISO alpha-3, and M49 code.
- Accent- and case-insensitive country search.
- Immutable typed country, capital, city, coordinate, and source objects.
- Country collection behavior: indexing, membership, length, and iteration.
- UN region and subregion filters.
- Primary capitals with WGS84 coordinates, population, timezone, and GeoNames ID.
- Major cities over the configured population threshold.
- JSON-compatible serialization and explicit source references.

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Start here

   why
   installation
   quickstart
   playground

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Explore the atlas

   country_profile
   capitals_cities
   searching
   serialization

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Data and trust

   data_sources
   data_quality
   _generated/project_status
   roadmap

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Reference

   api
   migration
   changelog
