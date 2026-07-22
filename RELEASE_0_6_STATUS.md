# PyWorldAtlas 0.6.0 release status

Version 0.6.0 is the country-reference and discovery release. The package
version is 0.6.0, the schema version is 6, and the dataset identifier is
2026.07.22.6.

## Included

- 234 source-provided national-anthem title profiles.
- 32 reviewed source-listed national mottos.
- 227 English demonym profiles.
- Enriched currency and language models with source references.
- 417 country-level timezone records across 246 profiles.
- 176 postal-code formats.
- Exact currency, language, script, and timezone filters.
- Typed rankings and nearest-capital discovery.
- A revised documentation opening, focused guides, and runnable examples.

## Explicitly excluded

- Anthem lyrics, audio, contributor credits, and adoption/readoption dates.
- Context-free foundation dates or other unreviewed reference dates.
- Boundary geometry, GeoJSON, bounding boxes, centroids, and point-in-country.
- Political commentary, opinion, or qualitative comparisons of countries or
  people.

## Data and review boundary

Factbook extraction is limited to structured country-name, anthem-title, and
nationality fields. CLDR and IANA provide reference labels for captured currency
and language codes. GeoNames supplies country timezones and postal formats.
Every captured Wikidata motto statement has an explicit reviewed include or
exclude decision, and the public motto model does not infer legal status.

## Release acceptance criteria

- All snapshot checksums and exact coverage fixtures pass.
- Every runtime source has a declared field role and documented terms.
- All public objects are immutable, typed, serializable, and documented.
- Rankings have documented metrics, units, missing-value behavior, and stable
  ordering.
- Nearest-capital results use documented great-circle semantics.
- The complete examples, HTML documentation, doctests, clean-wheel install,
  source-distribution audit, and policy checks pass.
- The candidate is merged to `main` with green GitHub Actions before tagging.

## Publication sequence

Run `python maintain.py prepare-release 0.6.0`, commit and push the
`release/0.6.0` branch, merge its green pull request, then create and push the
annotated `v0.6.0` tag from the exact merged `main` commit. The tag workflow
publishes PyPI, creates the GitHub Release, and deploys the documentation site.
See `RELEASING.md` for exact commands and public verification checks.

## Validation

The complete local release gate passes with:

- 37 runtime, pipeline, and policy tests.
- 276 executable documentation examples.
- Strict Sphinx HTML generation.
- Clean installation and execution of every example from the built wheel.
- Wheel and source-distribution content audits.
- Reproducible offline database generation and exact source checksums.
