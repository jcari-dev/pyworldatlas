# Roadmap

PyWorldAtlas advances through installable, documented releases. Version 0.1.0
established the dependency-free runtime, generated database, and captured
248-country-and-area UN M49 scope.

Release 0.2.1 completed the rich-profile and coordinate milestone: population and
currency context, language and calling-code metadata, direct city coordinates,
dependency-free distance, bearing, and midpoint calculations, flag emoji,
discovery cards, stable sampling, and structured flashcards. It also includes
the first five reviewed official local names. Version 0.3.0
added 319 reviewed land borders, neighbors, shared neighbors, shortest paths,
crossing counts, connected components, and borderless-entity discovery. Version
0.3.1 adds explicit reachability checks, path name and code conveniences, and
graph-derived flashcards.

The 0.4 development milestone completed the country-identity layer. Its local display
layer covers all 248 countries and areas across 80 languages and 21 scripts.
Ten selected records currently add reviewed UNGEGN national official forms and
source-provided romanization. A separate sourced English formal-name layer
covers 240 profiles: 195 distinct long forms and 45 source-equal short/formal
forms, with eight explicit source-scope gaps. The declared data scope is
complete and merged to `main`. These features are included in version 0.5.0.

Version 0.5.0 publishes the completed country-identity work and establishes the
package's educational and editorial policy. It audits the public data model,
source roles, geographic conventions, examples, documentation, correction
process, and release gate. It adds no current-affairs, opinion, or speculative
narrative dataset.

Version 0.6.0 then considers sourced anthem titles, mottos, and clearly labelled
reference dates without lyrics or an oversimplified universal date field.
Geometry, statistics, institutions, exports, and full-world hardening follow.

`ROADMAP_STATUS.md` records generated evidence. The detailed execution boundary
and release gates live in the versioned `RELEASE_*_STATUS.md` files. The current
identity contract is `COUNTRY_IDENTITY_DATA_SPEC.md`; the governing editorial
contract is `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.
