# Contributing to PyWorldAtlas

PyWorldAtlas welcomes careful code, documentation, and factual corrections that
support its educational purpose. Contributions must follow
`EDUCATIONAL_AND_NEUTRALITY_POLICY.md` and `CODE_OF_CONDUCT.md`.

## Before proposing data

A data contribution should include:

- The affected field and country or area code.
- The proposed value in source-preserved text.
- A stable source name, URL, publication or snapshot date, and exact locator.
- The source's reuse terms.
- A short explanation of why the source is appropriate for that field.
- Any conflict with the current value or another retained source.
- A clear representation of missingness, uncertainty, or date precision.

Do not submit unsourced country summaries, opinion, anonymous compilations,
social-media claims, or inferred classifications. New field families require a
written source and editorial review before data collection begins.

## Discussing names and disputed geography

Address the documented source convention, field priority, topology rule, or
review record. Do not argue from national superiority, hostility, or assumptions
about another contributor's identity or motives. Source-backed corrections are
useful; campaigning and personal disputes are outside the repository's purpose.

## Development checks

From the repository root:

```console
python maintain.py refresh --offline
python maintain.py test
python maintain.py docs
```

Before a release candidate:

```console
python maintain.py prepare-release VERSION
```

Tests, examples, data coverage reports, documentation, source notices, and
release notes should change together when a public field changes.

## Pull requests

Keep a pull request focused. Describe its user-visible effect, source changes,
missing-data behavior, compatibility impact, and validation performed. Do not
include secrets, private reports, unrelated generated files, or personal data.
