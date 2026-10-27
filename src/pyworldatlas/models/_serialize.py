"""Convert public models to JSON-compatible primitives."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value
