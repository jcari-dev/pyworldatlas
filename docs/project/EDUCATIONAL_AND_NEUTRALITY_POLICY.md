# Educational and editorial policy

## Purpose

PyWorldAtlas is a purely educational package that provides offline access to
factual geographic data. It is intended for learners, teachers, developers,
researchers, and anyone who needs a compact geographic reference without a
network connection.

The project does not provide political commentary, promote a viewpoint, make
qualitative judgments about people or places, or decide geographic
disagreements. Its role is limited to presenting clearly defined data from
documented sources. Numeric ranking utilities only sort explicitly labelled
facts or transparent calculations; they are not measures of human or cultural
worth.

## Editorial commitments

PyWorldAtlas follows these commitments:

1. **Education first.** Every public field must have a clear learning or
   reference purpose.
2. **Factual scope.** Values must come from identified sources or transparent
   calculations over sourced values.
3. **Careful attribution.** A value represents the convention used by its
   cited source. Including it is not an endorsement of an organization or a
   broader interpretation.
4. **Respectful language.** Documentation and examples describe every person,
   place, language, and culture with care.
5. **Honest limitations.** Missing, conflicting, changing, or unavailable data
   remains missing or is explained clearly.
6. **Reproducibility.** Source versions, checksums, review decisions, and known
   limitations are retained so the data can be inspected.

## Source-selection policy

Sources are selected for a specific field, not for a general point of view.
The project prefers established standards bodies, international statistical
and naming publications, openly licensed geographic datasets, and primary
institutional records when they are appropriate for the field.

No source is presented as universally neutral or complete. Names, boundaries,
and statistics can vary between institutions or change over time. PyWorldAtlas
handles this through attribution, narrow field definitions, independent
cross-checks where useful, and published limitations. Commentary, anonymous
compilations, unsupported claims, and advocacy material are not used as
authorities for the bundled dataset.

## Country names, areas, and borders

The words *country* and *area* are practical dataset labels. They are not
statements about recognition or status. Names, classifications, and land-border
relationships follow the documented source snapshots and review rules.

Other institutions may use different conventions. PyWorldAtlas records its
chosen convention so results are reproducible; it does not ask users to adopt
that convention outside the package.

## Publication boundaries

The package focuses on stable geographic reference fields such as identifiers,
names, languages, writing systems, capitals, populated places, coordinates,
distances, regions, currencies, calling codes, internet domains, and reviewed
geographic relationships. Source-aware anthem titles, mottos, demonyms,
timezones, and postal formats may be included when their exact field boundary
and coverage are documented.

Current affairs, political opinion, disputed interpretation, comparisons of
human worth, and speculative narrative are outside the dataset. A future field
must have a precise educational use, suitable reuse terms, dependable sources,
and a documented review method before it can be considered.

## Official statistics

Statistics (planned for 0.12) follow stricter rules than other fields, because
numbers about countries are easy to read as judgements.

1. **Publishers.** Only international statistical publishers: the United
   Nations (Statistics Division and the Population Division of DESA) and the
   World Bank (World Development Indicators). Values are used exactly as
   published, apart from documented unit conversion.
2. **Every value is labelled.** Each value carries its indicator code, unit,
   reference year, publisher, and snapshot date. Estimates and projections are
   labelled as such, and a projection is never presented as an observation.
3. **Basic, descriptive indicators only.** Indicators describe population,
   land, environment, health, education, and infrastructure in plain physical
   or counted terms, such as population, life expectancy at birth, forest area,
   or the share of people with electricity. A new indicator needs a stated
   learning purpose.
4. **Out of scope.** Composite indices and scores of any kind; governance,
   corruption, freedom, rights, or "fragility" measures; military, conflict,
   crime, or security data; religion or ethnicity; migration and refugee
   counts; aid, debt, and poverty or inequality measures; and any indicator
   whose name or definition carries a judgement. When an indicator is in
   doubt, it is left out.
5. **No judgement in presentation.** Statistics may be listed, charted, and
   sorted, but never labelled better or worse. Map colors use one neutral,
   ordered scale with no good or bad colors, and sorted lists say only what
   was sorted and in which direction.
6. **Missing stays missing.** Gaps are never filled by estimation, carried
   forward from other years, or borrowed from another publisher. Regional and
   world totals are shown only as published.
7. **Pinned and dated.** Each statistics pack pins a dated snapshot.
   Publishers revise past values, so a value can differ from the publisher's
   current release; the snapshot date says which release was used.

## Classroom and public use

PyWorldAtlas is designed for classrooms, tutorials, portfolios, research
prototypes, and general-purpose software. Applications should preserve source
and coverage notes when presenting fields that can vary between institutions.
Teaching source literacy is encouraged: a sourced value can be useful without
being the only convention in use.

## Corrections and accountability

Factual corrections are welcome. A correction should identify the affected
field and record, the proposed value, a dependable source, the source date, and
the reason the current value is inaccurate within the documented scope.
Consequential naming and border changes are recorded rather than changed
silently.

Respect is required throughout the project. Hateful, harassing, threatening,
demeaning, or discriminatory content is not accepted. The complete community
standard is in `CODE_OF_CONDUCT.md`.

## Version 0.5.0 policy milestone

Version 0.5.0 establishes and audits this educational scope. It adds no
political commentary or opinion dataset. Its release gate checks public fields,
source roles, documentation, examples, contribution guidance, correction
procedures, and release contents against this policy.
