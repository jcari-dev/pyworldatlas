# 0.2.0 development baseline

This snapshot records the tagged 0.1.0 source state before 0.2.0 work began. It
is the comparison point for package size, database size, performance, and
compatibility.

| Check | Baseline |
|---|---:|
| Unit tests | 13 passing |
| Countries and areas | 248 |
| Major cities | 6,265 |
| Wheel size | 375,654 bytes |
| SQLite size | 757,760 bytes |
| Fresh-process import, median | 94.179 ms |
| First `Atlas()` open, median | 0.712 ms |
| Country lookup, median | 1.290 ms |
| Iterate all countries, median | 33.115 ms |
| Serialize all countries, median | 26.915 ms |

The measurements use Python 3.12.13 and seven runs per timing. They are local regression indicators rather than cross-machine performance promises.

## Quality gate

- All 13 unit tests passed.
- `playground.py` audited every exposed country, capital, and city record.
- Fresh wheel and source distributions built successfully.
- Both packaged examples passed in an isolated, offline environment.
- Sphinx HTML passed with warnings treated as errors.
- All 79 documentation tests passed.
- The wheel-content audit passed.
