# PyWorldAtlas 0.5.0 release status

Version 0.5.0 combines the merged country-identity milestone with a formal
educational and editorial policy. The package version is 0.5.0, the schema
version is 5, and the dataset identifier is 2026.07.21.5.

## Purpose

PyWorldAtlas is a purely educational package that provides offline access to
factual geographic data. It does not provide political commentary, promote a
viewpoint, make qualitative judgments about people or places, or decide
geographic disagreements.

## Included

- Sourced country identities, English formal names, local-language display
  names, reviewed official forms, language metadata, and writing systems.
- Formal educational and editorial policy.
- Respectful community and contribution standards.
- Field-specific source-selection and factual-correction guidance.
- Clear naming and border-data limitations.
- Automated checks for public-field scope, source roles, policy publication,
  documentation, and release contents.

## Dataset boundary

Version 0.5.0 adds no current-affairs, opinion, or speculative narrative data.
The country facts are the reviewed identity and geographic records completed in
the 0.4 development milestone. Dataset version 2026.07.21.5 records the updated
provenance registry and release-policy metadata. Schema 5 removes the unused
entity-status column so the public model contains only fields in active use.

## Release acceptance criteria

- Every public field has a clear educational or reference purpose.
- Every runtime source has a declared, narrow field role.
- Documentation and examples use respectful, factual language.
- Naming and land-border conventions are attributed and limited to their
  documented source scope.
- Policy, conduct, contribution, source, quality, and limitation documents are
  included in the source distribution.
- Runtime, pipeline, policy, documentation, clean-wheel, and release-content
  audits pass from the candidate branch.

## Validation

The complete local release gate covers:

- 34 runtime, pipeline, and policy tests.
- Clean installation and execution from the built wheel.
- Strict Sphinx HTML and documentation examples.
- Wheel and source-distribution content audits.
- Deterministic offline data rebuilding and coverage reports.

Passing locally makes the branch release-ready. Publication still requires a
reviewed pull request, green GitHub Actions, a merge to `main`, and the signed
`v0.5.0` tag described in `RELEASING.md`.
