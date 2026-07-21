# Official local-name pilot checkpoint

This checkpoint records the Brazil/Switzerland official-local-name pilot before
the remaining 0.2.0 profile and coordinate work. The records pass from the
captured UNGEGN artifact through reviewed normalized data, schema 2, the bundled
SQLite database, runtime models, serialization, documentation, and the wheel.

## Coverage and verification

| Measure | Result |
|---|---:|
| Countries and areas retained | 248 |
| Official local-name records | 5 |
| Pilot countries | 2 |
| Unit tests | 17 passing |
| Documentation tests | 90 passing |
| Full data audit | Passing |
| Fresh wheel and source distribution | Passing |
| Isolated offline wheel examples | Passing |
| Sphinx warnings-as-errors build | Passing |
| Wheel-content audit | Passing |

## Baseline comparison

| Measure | 0.1.0 baseline | 0.2.0 pilot | Change |
|---|---:|---:|---:|
| Wheel | 375,654 B | 377,656 B | +2,002 B (+0.533%) |
| SQLite | 757,760 B | 765,952 B | +8,192 B (+1.081%) |
| Unit tests | 13 | 17 | +4 |
| Doctests | 79 | 90 | +11 |

Median local timings were lower in this run for import, first open, lookup,
complete iteration, and complete serialization. Because these are short,
machine-local measurements, they show that no regression was detected; they do
not establish performance on other systems.

## Contract conclusions

- Search aliases and official local names remain separate data families.
- Countries without pilot coverage return an empty tuple and no fallback.
- Romanization is never generated.
- Unicode short and formal names survive JSON serialization.
- Materialized country records remain valid after the atlas closes.
- Collection iteration performs one bulk local-name query.
- Existing 0.1.0 lookup, collection, capital, city, and missing-value tests pass.

This is a historical checkpoint. The later 0.2.0 release candidate kept the
five reviewed records and added country profile metadata and coordinate tools.
