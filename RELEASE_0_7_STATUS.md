# PyWorldAtlas 0.7.0 release status

Version 0.7.0 is the physical-geography release. The package version is 0.7.0,
the schema version is 7, and the dataset identifier is 2026.07.22.7.

## Included

- Total area for 248 profiles, with sourced land/water components where
  available.
- Coastline for 238 profiles, named highest and lowest points for 240, and mean
  elevation for 166.
- 188 source-listed major river records across 80 profiles and 187
  source-listed major lake records across 69 profiles.
- 240 plain-language climate summaries and represented 1991–2020
  Köppen-Geiger classes for 241 profiles.
- Typed physical models, exact filters, feature-discovery helpers, rankings,
  discovery-card fields, and deterministic flashcards.
- Pinned source inputs, deterministic extraction, exact coverage gates, and a
  dedicated physical-geography guide.

## Explicitly excluded

- Country boundary geometry, GeoJSON, bounding boxes, centroids, and
  point-in-country lookup.
- A separate major-mountain inventory. Highest points remain typed as elevation
  points without inventing a global “major” threshold.
- Site-level climate determination, forecasting, and unreviewed climate labels.
- Political commentary, opinion, or qualitative comparisons of countries or
  people.

## Data and review boundary

Structured physical fields come from the pinned public-domain Factbook
snapshot. River and lake tuples are source-listed major features rather than
exhaustive inventories; shared-feature measurements describe the whole feature.
Köppen-Geiger classes are latitude-area-weighted country aggregations from the
CC0 0.1-degree 1991–2020 raster and public-domain Natural Earth map units.
Classes below 0.1% of represented profile area are omitted.

## Release acceptance criteria

- All source and derived checksums and exact coverage fixtures pass.
- Every runtime source has a declared field role and documented terms.
- All public physical objects are immutable, typed, serializable, and
  documented.
- Filters, rankings, feature search, and learning prompts have deterministic,
  documented missing-value behavior.
- The complete examples, HTML documentation, doctests, clean-wheel install,
  source-distribution audit, and policy checks pass.
- The candidate is merged to `main` with green GitHub Actions before tagging.

## Publication sequence

Run `python maintain.py prepare-release 0.7.0`, commit and push the
`release/0.7.0` branch, merge its green pull request, then create and push the
annotated `v0.7.0` tag from the exact merged `main` commit. The tag workflow
publishes PyPI, creates the GitHub Release, and deploys the documentation site.
See `RELEASING.md` for exact commands and public verification checks.

## Validation

The complete local release gate passes with:

- 39 runtime, pipeline, and policy tests.
- 303 executable documentation examples.
- Strict Sphinx HTML generation with warnings treated as errors.
- Clean installation and execution of every example from the built wheel.
- Wheel and source-distribution content and policy audits.
- Reproducible offline database generation and exact source checksums.
- A visual review of the generated documentation homepage and physical-
  geography guide.
