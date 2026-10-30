"""Spelling suggestions for "Did you mean ...?" error messages.

Only error paths use this module, so normal lookups never pay for it. It uses
the standard library's ``difflib``, which compares letters the way a person
would notice a typo ("Japn" is one letter from "Japan").
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from difflib import SequenceMatcher

from ._normalization import normalize_name

CUTOFF = 0.75
"""How alike two spellings must be (0 to 1) before one is suggested for the other."""


def similarity(query: str, name: str) -> float:
    """Return how alike ``query`` is to ``name`` or to any single word of it.

    Comparing words as well lets "Everst" find "Mount Everest", where the
    whole name is too different but one word is a near match. A word match
    counts slightly less than a whole-name match, so "Tokio" puts "Tokyo"
    before "Nishi-Tokyo-shi", and words shorter than the query are skipped,
    so "Japn" does not suggest "Jan Mayen".
    """
    wanted = normalize_name(query)
    full = normalize_name(name)
    best = SequenceMatcher(None, wanted, full).ratio()
    for word in full.split():
        if len(word) >= len(wanted) and word != full:
            best = max(best, 0.98 * SequenceMatcher(None, wanted, word).ratio())
    return best


def closest(query: str, names: Iterable[str], *, limit: int = 3) -> list[str]:
    """Return up to ``limit`` distinct names that look like ``query``, closest first."""
    scored: dict[str, float] = {}
    for name in names:
        score = similarity(query, name)
        if score >= CUTOFF and score > scored.get(name, 0.0):
            scored[name] = score
    return sorted(scored, key=lambda name: (-scored[name], name))[:limit]


def by_prefix(query: str, search: Callable[[str], Iterable[str]], *, limit: int = 3) -> list[str]:
    """Suggest names for a large index that can only be searched by text.

    Shorter and shorter beginnings of the query are searched ("Everst",
    "Evers", "Ever", "Eve"), and the closest of all the candidates are kept,
    so "Everst" finds "Mount Everest" even though "Everson" appears first.
    This keeps suggestions fast over 200,000 places without scanning them all.
    """
    text = normalize_name(query)
    candidates: dict[str, None] = {}  # keeps the first-seen order, like an ordered set
    for length in range(len(text), 2, -1):
        candidates.update(dict.fromkeys(search(text[:length])))
    return closest(query, candidates, limit=limit)


def choice(value: str, choices: Iterable[str]) -> str | None:
    """Return the choice ``value`` means, forgiving case, spaces, and plurals.

    ``"Capital"``, ``"capital"``, and ``"capitals"`` all mean ``"capitals"``;
    ``"plug types"`` means ``"plug_types"``. Returns ``None`` when nothing fits.
    """
    # Compare in lower case but return the choice as written, so "cfb"
    # finds the climate code "Cfb".
    options = {option.casefold(): option for option in choices}
    key = value.strip().casefold().replace(" ", "_").replace("-", "_")
    for candidate in (key, f"{key}s", f"{key}es", key.removesuffix("s")):
        if candidate in options:
            return options[candidate]
    return None


def did_you_mean(names: list[str]) -> str:
    """Return a sentence such as ``" Did you mean Japan?"``, or ``""`` for no names."""
    if not names:
        return ""
    if len(names) == 1:
        return f" Did you mean {names[0]}?"
    return f" Did you mean {', '.join(names[:-1])} or {names[-1]}?"
