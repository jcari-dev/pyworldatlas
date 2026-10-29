"""How results look when printed: short by default, every field on request.

Every result prints as one readable line, such as
``CountryRanking('#1 Russia: 17,098,242 km²')``. Turn on details to see every
field instead, as plain Python dataclasses show them::

    import pyworldatlas
    pyworldatlas.show_details()           # from now on
    with pyworldatlas.show_details():     # only inside this block
        ...

Setting the environment variable ``PYWORLDATLAS_DETAILS=1`` turns details on
from the start. Details change only how results are printed, never their
values, and ``to_dict()`` always returns every field.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import os
from typing import Any

_STATE = {"details": os.environ.get("PYWORLDATLAS_DETAILS", "").strip().casefold() not in {"", "0", "false", "no"}}


class show_details:  # named like a function because it is used like one
    """Print every field of a result instead of the short one-line form.

    ``show_details()`` turns details on, ``show_details(False)`` turns them
    off, and ``with show_details(): ...`` turns them on only inside the block.

    >>> import pyworldatlas
    >>> with pyworldatlas.show_details():
    ...     pass
    """

    def __init__(self, on: bool = True) -> None:
        self._previous = _STATE["details"]
        _STATE["details"] = bool(on)

    def __enter__(self) -> show_details:
        return self

    def __exit__(self, *exc_info: object) -> None:
        _STATE["details"] = self._previous


def details_shown() -> bool:
    """Return whether results currently print every field."""
    return _STATE["details"]


def friendly_repr(value: Any, short: str) -> str:
    """Return ``Name(short)``, or ``Name(field=value, ...)`` when details are on.

    ``short`` is the readable inside of the repr, already quoted where it is
    text, such as ``"'#1 Russia: 17,098,242 km²'"``.
    """
    name = type(value).__name__
    if _STATE["details"] and is_dataclass(value):
        parts = ", ".join(f"{field.name}={getattr(value, field.name)!r}" for field in fields(value) if field.repr)
        return f"{name}({parts})"
    return f"{name}({short})"
