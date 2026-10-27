"""Learning-tool models: flashcards, quiz questions, and discovery cards."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ._serialize import _jsonable
from .reference import Currency, LocalizedName
from .geography import Coordinate, ElevationPoint
from .results import CountryReference


@dataclass(frozen=True, slots=True)
class Flashcard:
    """A deterministic geography study prompt and answer.

    Flashcards contain no scoring, session state, or hidden random state. The
    ``topic`` value identifies the documented generator used by
    :meth:`pyworldatlas.Atlas.flashcards`.
    """

    topic: str
    prompt: str
    answer: str
    country: CountryReference

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this flashcard."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this flashcard as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class QuizQuestion:
    """A deterministic multiple-choice geography question.

    Choices are stored in display order and ``answer`` is always one of them.
    Use :attr:`answer_number` for a one-based classroom answer key or
    :meth:`is_correct` to check either a displayed answer or choice number.
    """

    topic: str
    prompt: str
    choices: tuple[str, ...]
    answer: str
    country: CountryReference

    def __post_init__(self) -> None:
        if len(self.choices) < 2:
            raise ValueError("a quiz question must contain at least two choices")
        normalized = tuple(choice.casefold() for choice in self.choices)
        if len(set(normalized)) != len(normalized):
            raise ValueError("quiz choices must be unique")
        if self.answer not in self.choices:
            raise ValueError("answer must be present in choices")

    @property
    def answer_number(self) -> int:
        """Return the correct choice number using one-based classroom numbering."""
        return self.choices.index(self.answer) + 1

    def is_correct(self, choice: str | int) -> bool:
        """Check an answer string or a one-based choice number.

        Text matching ignores surrounding whitespace and letter case. Invalid
        choice numbers return ``False``; unsupported input types raise
        :class:`TypeError`.
        """
        if isinstance(choice, bool):
            raise TypeError("choice must be an answer string or one-based integer")
        if isinstance(choice, int):
            return 1 <= choice <= len(self.choices) and self.choices[choice - 1] == self.answer
        if isinstance(choice, str):
            return choice.strip().casefold() == self.answer.strip().casefold()
        raise TypeError("choice must be an answer string or one-based integer")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this question."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this question without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class CountryDiscoveryCard:
    """A compact, serializable teaching view of one materialized country.

    Every value is copied from, or calculated directly from, an existing
    :class:`Country`. Creating a card never queries the database or network.
    """

    country: CountryReference
    flag_emoji: str | None
    official_name: str | None
    formal_name: str | None
    capital: str | None
    capital_coordinates: Coordinate | None
    continent: str | None
    region: str | None
    subregion: str | None
    population: int | None
    area_km2: float | None
    population_density: float | None
    currency: Currency | None
    language_codes: tuple[str, ...]
    calling_codes: tuple[str, ...]
    top_level_domain: str | None
    observed_timezones: tuple[str, ...]
    local_names: tuple[LocalizedName, ...]
    major_city_count: int
    source_ids: tuple[str, ...]
    anthem_title: str | None = None
    motto_text: str | None = None
    demonym: str | None = None
    timezone_ids: tuple[str, ...] = ()
    coastline_km: float | None = None
    highest_point: ElevationPoint | None = None
    climate_zone_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this discovery card."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this discovery card as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
