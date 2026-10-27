# Contributing to PyWorldAtlas

Thank you for helping make offline geography easier to explore and teach.
Questions and focused contributions are welcome from first-time contributors
and experienced maintainers alike.

All participation follows the
[educational and neutrality policy](docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md) and
[code of conduct](CODE_OF_CONDUCT.md).

## Good ways to contribute

- Report a reproducible package bug.
- Propose a factual correction with a reliable source.
- Improve an explanation, example, docstring, or classroom activity.
- Suggest a focused feature through a concrete Python example.
- Strengthen tests, validation, accessibility, or packaging.

Use the repository issue forms so maintainers receive the information needed to
review the report. Security concerns follow [SECURITY.md](SECURITY.md), not the
public bug tracker.

## Development setup

Create and activate a virtual environment with Python 3.10 or newer, then run:

```console
python maintain.py bootstrap
python maintain.py test
python maintain.py docs
```

Install the development-only checking tools once. They are never runtime
dependencies; PyWorldAtlas itself uses only the Python standard library.

```console
python -m pip install -r requirements-dev.txt
python maintain.py quality
```

`quality` runs Ruff, strict mypy, and the test suite under branch coverage, and
fails below 90% coverage.

The test suite includes a public API snapshot (`tests/api_snapshot.json`). When
a change to the public API is intentional, update it with
`PYWORLDATLAS_UPDATE_API_SNAPSHOT=1 python -m unittest discover -s tests` and
explain the change in the pull request.

Before submitting a pull request, run the complete gate:

```console
python maintain.py check
```

The complete gate runs the quality checks (when the tools are installed), builds
all four package distributions, installs the wheels in isolation, executes the
examples, builds strict documentation and doctests, and audits release contents,
including the `py.typed` marker.

## Factual corrections

A data correction should include:

- The affected country or area and field.
- The current value and proposed value.
- A stable source name, URL, publication or snapshot date, and exact locator.
- The source's reuse terms.
- A short explanation of why the source is appropriate for that field.
- Any conflict with another retained source.

Do not submit unsourced summaries, opinion, anonymous compilations,
social-media claims, or inferred classifications. Missingness and uncertainty
must remain explicit. New field families require source and editorial review
before collection begins.

## Names, areas, and borders

Address the documented source convention, field priority, topology rule, or
review record. Source-backed corrections are useful; advocacy, hostility, and
personal disputes are outside the repository's educational purpose.

## Pull-request checklist

- Keep the change focused and explain its user-visible effect.
- Add or update tests for changed behavior.
- Update examples, documentation, and provenance when public data changes.
- Preserve supported Python versions and the dependency-free runtime unless a
  proposal explicitly justifies changing them.
- Do not commit secrets, private reports, local environments, build products,
  or unrelated generated files.
- Confirm `python maintain.py check` passes.

Release publication is performed by maintainers using the
[release process](docs/project/RELEASING.md).
