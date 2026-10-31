"""Keep printed results working when output goes to a legacy code page.

Results print with symbols such as ``→``, ``·``, ``°``, and ``²``. On Windows,
output redirected to a file or pipe uses the legacy code page (often cp1252),
which cannot encode them, so ``print(result)`` would raise
``UnicodeEncodeError``. When a standard stream cannot encode these symbols, it
is switched to UTF-8, as the ``pyworldatlas`` command already does.
"""

from __future__ import annotations

import io
import sys

_SYMBOLS = "→·°²"


def ensure_printable() -> None:
    """Switch stdout and stderr to UTF-8 if they cannot print atlas results."""
    for stream in (sys.stdout, sys.stderr):
        if not isinstance(stream, io.TextIOWrapper):
            continue
        try:
            _SYMBOLS.encode(stream.encoding)
        except (UnicodeEncodeError, LookupError):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass
