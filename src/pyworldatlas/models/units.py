"""Small value types that print themselves clearly: distances and summaries."""

from __future__ import annotations

from collections.abc import Callable

UNITS = ("km", "mi", "nmi")
"""Kilometres, statute miles, and nautical miles."""


class Distance(float):
    """A great-circle distance that is still a plain number.

    ``Distance`` behaves exactly like a ``float`` (add it, compare it, round
    it, or save it to JSON), and also remembers its ``unit``. Printing it gives
    friendly text such as ``"9,713 km"``; distances under 10 keep one decimal,
    such as ``"0.3 km"``.

    >>> from pyworldatlas import Distance
    >>> distance = Distance(9712.518, "km")
    >>> print(distance)
    9,713 km
    >>> distance > 9000
    True
    """

    unit: str

    def __new__(cls, value: float, unit: str = "km") -> Distance:
        if unit not in UNITS:
            raise ValueError("unit must be 'km', 'mi', or 'nmi'")
        distance = super().__new__(cls, value)
        distance.unit = unit
        return distance

    @property
    def text(self) -> str:
        """Return the distance as friendly text, such as ``"9,713 km"``."""
        decimals = 1 if abs(self) < 10 else 0
        return f"{float(self):,.{decimals}f} {self.unit}"

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        from ._display import details_shown

        number = repr(float(self)) if details_shown() else f"{float(self):.1f}"
        return f"Distance({number}, {self.unit!r})"

    def __reduce__(self) -> tuple[type[Distance], tuple[float, str]]:
        # Lets copy and pickle rebuild the unit as well as the number.
        return (Distance, (float(self), self.unit))


class SummaryText(str):
    """Text that can also be called, so ``country.summary`` and ``country.summary()`` both work.

    Summaries are properties on every result. Country summaries used to be a
    method; calling one still works, and ``country.summary(local_language="fr")``
    still chooses which local name to show.
    """

    _build: Callable[..., str]

    def __new__(cls, text: str, build: Callable[..., str]) -> SummaryText:
        summary = super().__new__(cls, text)
        summary._build = build
        return summary

    def __call__(self, **options: str | None) -> str:
        return self._build(**options) if options else str(self)
