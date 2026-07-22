# PyWorldAtlas 0.4.0 development status

Version 0.4.0 is the country-identity milestone. Its declared data layers are
implemented and the local release gate passes. It remains a development
candidate until the changes are committed, reviewed, and published.

## Implemented

- One sourced local identity for all 248 countries and areas.
- Sourced English formal names for 240 profiles: 195 distinct long forms and
  45 cases where the source uses the short form as the formal identity.
- Eight explicit English formal-name gaps outside the captured source
  intersection: AX, BQ, GF, GP, MQ, RE, UM, and YT.
- 80 represented languages and 21 ISO 15924 scripts.
- 244 selections in an official, de-facto official, or regional official
  language; four explicit non-applicable/administrative exceptions.
- 10 selected records upgraded to reviewed UNGEGN national official short and
  formal names.
- Reviewed national short and formal names in original Unicode text.
- Source-provided romanized short and formal names when available.
- Per-record source references and exact CLDR locale/XPath or UNGEGN entry/page
  locators.
- `LocalizedName.kind`, `language_status`, `formal_name`, and `source_locator`.
- `Country.local_name(language_code)`.
- `Country.formal_name` and `Country.has_distinct_formal_name`.
- `Country.local_name_languages`.
- `Country.romanized_official_name_in(language_code)`.
- `Atlas.countries_with_local_names()` with language and script filters.
- `Atlas.countries_with_formal_names()`.
- Multilingual tests, flashcards, serialization checks, and an executable
  country-identity example.

The current UNGEGN replacements cover Brazil, Chile, China, Dominican Republic,
France, Iceland, India, Japan, Senegal, and Switzerland. The other 238 records
remain clearly labelled CLDR display names.

The English formal-name layer is separate. It uses the public-domain World
Factbook as its base, five current UN Protocol excerpts, and three exact
Wikidata CC0 statements. It does not promote CLDR labels or infer values for
the eight uncovered areas.

## Current version boundary

- Library version: `0.4.0`
- Schema version: `4`
- Dataset version: `2026.07.21.4`
- Runtime dependencies: `0`
- Supported Python versions: 3.10 through 3.14

Schema 4 records the evidence kind and language-selection status so a localized
display label cannot be confused with a reviewed national formal name.

## Review rules

Each CLDR row is generated deterministically from the pinned 48.2 archive and
must include country, selected language, script, local name, language status,
source locale, and XPath. The builder requires exactly 248 unique records.

Each UNGEGN replacement must be visually checked against the captured PDF and
must include country, language, script, short name, formal name, source, and
page locator. Romanization is stored only when printed by the source.

Right-to-left entries are reviewed separately. Extracted PDF text alone is not
accepted because bidirectional layout can reverse or drop characters.

## Remaining before release

- Perform a final human review of documentation examples and source claims.
- Commit the candidate, review the branch diff, and merge it through the normal
  repository workflow.
- Publish the GitHub release, PyPI distribution, and documentation site from the
  reviewed tag.

Expanding the 10-record national-official local layer is valuable later work,
but it is no longer a hidden prerequisite for the declared 0.4.0 coverage.

## Local validation result

On 2026-07-21, ``python maintain.py prepare-release 0.4.0`` passed all 30
runtime/pipeline tests, a clean wheel installation, every executable example,
strict Sphinx HTML, 221 doctests, and the release wheel-content audit.

National anthem titles, mottos, and clearly labelled civic events are specified
for the next minor release. They are not part of the 0.4.0 public API.

## Development gate

During batch development, run:

```console
python maintain.py refresh --offline
python maintain.py test
python maintain.py docs
```

The release gate may be run during development as a quality check:

```console
python maintain.py prepare-release 0.4.0
```

Passing it confirms the local release candidate. Publishing still requires a
reviewed commit, release notes, and the normal GitHub/PyPI release workflow.
