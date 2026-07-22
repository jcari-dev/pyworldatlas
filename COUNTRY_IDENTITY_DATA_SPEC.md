# Country identity data specification

## Purpose

The country-identity dataset records canonical English identities, sourced
English formal names, and one selected local identity for every country or
area. It is designed for accurate display, search, education, and serialization
without guessing a constitutional name, translation, or romanization.

The 0.4 development milestone completed the official-name layer. Version 0.5.0
published that work with the educational and editorial audit. Version 0.6.0
adds a deliberately smaller country-reference contract: anthem titles,
reviewed source-listed mottos, demonyms, and practical profile metadata.

## Country-identity release boundary

The release has three explicit coverage layers:

1. All 248 countries and areas receive a canonical English identity from the
   captured UN M49 scope.
2. 240 profiles receive a sourced English formal name. The public-domain World
   Factbook supplies the base layer; eight reviewed exceptions use current UN
   Protocol excerpts or exact Wikidata CC0 statements. Eight areas outside the
   source intersection remain `None`.
3. All 248 records receive one Unicode CLDR local display name and a
   deterministic language selection. Ten selected records are upgraded to
   reviewed UNGEGN national official short and formal names.

All three declared layers are complete at their stated coverage. The narrower
UNGEGN local-formal layer may expand in later reviewed batches, but it is never
presented as complete national-official coverage.

Every local identity row must have:

- A country in the canonical UN M49 scope.
- A language code and human-readable language name.
- An ISO 15924 script code.
- A sourced local display name.
- An explicit official-language flag.
- A captured source identifier and exact entry/page locator.
- An evidence kind: `locale_display` or `national_official`.

A `national_official` row additionally requires a formal name and retains
source-provided romanization when printed. A `locale_display` row leaves those
fields empty rather than promoting a localized label into a diplomatic name.

Countries or areas outside UNGEGN's independent-country scope remain explicit
local-formal coverage gaps. Their CLDR display names remain available and are
never relabelled as national formal names.

## English public name model

The three English fields answer different questions:

| Field | Meaning |
|---|---|
| `Country.name` | Familiar English display and lookup name used by the atlas |
| `Country.official_name` | Canonical English identity retained from UN M49 |
| `Country.formal_name` | Sourced English long/formal name, or `None` outside the source scope |

`Country.has_distinct_formal_name` is true only when the sourced formal form
differs from `Country.name`. A false value can mean either “same as the short
form” or “not covered”; inspect `Country.formal_name` to distinguish them.

English formal names are also indexed for exact country lookup. Use
`Atlas.countries_with_formal_names()` to discover the 240 covered profiles.

## Local public name model

`LocalizedName` represents one sourced local-language record:

| Field | Meaning |
|---|---|
| `short_name` | Selected local display name or reviewed national short form |
| `formal_name` | Reviewed national official formal form, when available |
| `language_code` | Normalized language identifier |
| `language_name` | English display name for the language |
| `script_code` | ISO 15924 script identifier |
| `romanized_short_name` | Source-printed romanization, when present |
| `romanized_official_name` | Source-printed formal romanization, when present |
| `is_official_language` | Whether the source lists the language as national official |
| `language_status` | CLDR selection status such as official, de-facto official, or not applicable |
| `kind` | `locale_display` or `national_official` evidence level |
| `source` | Captured source reference |
| `source_locator` | Exact CLDR locale/XPath or UNGEGN entry/PDF page |

On `LocalizedName`, the existing `official_name` attribute remains available
for compatibility; `formal_name` is its clearer read-only alias. These are
language-specific values and are separate from `Country.formal_name`.

## Public API contract

```python
country.local_names
country.local_name("es")
country.local_name_languages
country.name_in("es")
country.official_name_in("es")
country.romanized_name_in("zh")
country.romanized_official_name_in("zh")

atlas.countries_with_formal_names()
atlas.countries_with_local_names()
atlas.countries_with_local_names(language_code="es")
atlas.countries_with_local_names(script_code="Jpan")
atlas.countries_with_local_names(name_kind="national_official")
```

Language and script filters are case-insensitive exact matches. All results are
immutable and detached from SQLite. A missing local formal name means “not in
the reviewed UNGEGN layer,” not “this name does not exist.” A missing English
``Country.formal_name`` means the profile is outside the captured source
intersection.

## Transcription and normalization rules

- Preserve national-script text as Unicode and write source files as UTF-8.
- Normalize language and country codes, not the spelling of names.
- Omit parenthetical grammatical articles printed for UN editorial use, such as
  `(the)`, `(la)`, or `(le)`.
- Retain accents, case, punctuation, and source-provided romanization.
- Remove note markers from values and retain the note reference in the source
  locator.
- Do not transliterate, translate, modernize, or silently correct a source form.
- Treat multiple valid source forms as data, not as a choice for the builder to
  resolve without a review record.

## Source and review policy

Complete display-name coverage comes from the pinned Unicode CLDR 48.2 release.
The compact extracted snapshot retains the archive URL and checksum, exact
locale/XPath locators, language-selection metadata, and Unicode License v3.

National official forms come from the captured United Nations Group of Experts
on Geographical Names country-name document dated 17 July 2017. Its PDF, URL,
retrieval date, byte size, and SHA-256 checksum are preserved under
`build_data/raw/ungegn-country-names/`.

Reviewed UNGEGN transcriptions live in
`build_data/reviewed/country_local_names.csv`. The offline builder overlays the
matching selected CLDR record and emits exactly one local identity per country
or area. It rejects unknown or duplicate codes, incomplete rows, invalid flags,
non-NFC text, and any coverage count other than 248.

Right-to-left and complex-script entries require visual review of the rendered
source page. Text extraction alone is not acceptable evidence.

English formal names use a compact public-domain extraction of the final
structured CIA World Factbook country-name profiles. Five current names are
short credited excerpts from the United Nations Protocol and Liaison Service
list, and three are exact Wikidata ``official name`` statements released under
CC0. The reviewed override CSV records each source locator and decision. The
UNTERM export was used only as a private comparison during review and is not
redistributed or copied into the package.

## Coverage reporting

Generated reports must expose at least:

- Local identity records and countries covered.
- English formal-name records, distinct long forms, short-equals-formal forms,
  and uncovered codes.
- CLDR display names versus reviewed national official names.
- Official-language selections and explicit exceptions.
- Languages represented.
- Scripts represented.
- Records with source-provided romanization.
- The countries in scope that still have no reviewed record.

Documentation must place these numbers beside every coverage claim.

## Version 0.6.0: country reference facts

The 0.6 models are optional, immutable, source-aware records. Missing coverage
remains explicit.

### National anthem

- Source title and optional source-provided English title.
- Per-record source reference and exact locator.
- No lyrics, audio, contributor credits, adoption dates, or narrative history.

### National motto

- Selected source label and language code.
- English label when the captured statement supplies one.
- Per-record source reference and exact statement locator.
- An explicit review decision for every captured statement.
- No inferred official, traditional, constitutional, statutory, or current
  legal status.

### Demonym

- Source-preserved English noun and adjective forms.
- Per-record source reference and exact locator.
- No generated gender, number, local-language, or alternate forms.

### Practical metadata

- Currency name, common symbol, and minor-unit digits.
- Language English name and likely script.
- Country-level timezone records and captured offsets.
- Postal-code display format and optional source regular expression.

### Deferred reference dates

A country does not receive one context-free `foundation_date`. Instead, each
record identifies the event it dates, for example:

- Independence declared.
- Independence recognized.
- Constitution effective.
- State established or unified.
- United Nations admission.

Dates would retain year, month, or day precision exactly as supported by the
source. They are not part of 0.6.0 because a uniform source and review contract
has not been approved.

## Release rule

The 0.6 reference layer ships only after exact source checksums, motto decisions,
declared coverage, typed-model tests, examples, HTML documentation, doctests,
wheel smoke tests, policy checks, and source audits all pass.
