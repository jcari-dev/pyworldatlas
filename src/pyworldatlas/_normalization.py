"""Internal text normalization helpers."""

from __future__ import annotations

import unicodedata


def normalize_name(value: str) -> str:
    """Return a case- and accent-insensitive lookup key."""
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join("".join(ch if ch.isalnum() else " " for ch in plain.casefold()).split())

