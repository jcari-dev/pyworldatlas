"""Describe the public Python API as plain data for the snapshot test.

The description covers every name exported by ``pyworldatlas`` and
``pyworldatlas.models``: class signatures, dataclass fields, public methods,
properties, and exception bases. Internal module locations are deliberately
left out, so code can move between private modules without changing the API.
"""

from __future__ import annotations

import dataclasses
import inspect
from typing import Any


def _signature(value: Any) -> str:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return "<no signature>"


def _members(cls: type) -> dict[str, str]:
    members: dict[str, str] = {}
    for name, raw in vars(cls).items():
        if name.startswith("_") and name not in {
            "__getitem__", "__contains__", "__len__", "__iter__",
            "__enter__", "__exit__",
        }:
            continue
        if isinstance(raw, property):
            members[name] = "property"
        elif isinstance(raw, staticmethod):
            members[name] = f"staticmethod{_signature(raw.__func__)}"
        elif isinstance(raw, classmethod):
            members[name] = f"classmethod{_signature(raw.__func__)}"
        elif callable(raw):
            members[name] = f"method{_signature(raw)}"
    return dict(sorted(members.items()))


def describe(value: Any) -> dict[str, Any]:
    """Return a JSON-compatible description of one public object."""
    if not isinstance(value, type):
        return {"kind": type(value).__name__, "value": repr(value)}
    if issubclass(value, BaseException):
        return {
            "kind": "exception",
            "bases": [base.__name__ for base in value.__mro__[1:]],
        }
    description: dict[str, Any] = {
        "kind": "dataclass" if dataclasses.is_dataclass(value) else "class",
        "signature": _signature(value),
        "members": _members(value),
    }
    if dataclasses.is_dataclass(value):
        params = value.__dataclass_params__  # type: ignore[attr-defined]
        description["frozen"] = params.frozen
        description["fields"] = [
            {
                "name": field.name,
                "type": str(field.type),
                "default": (
                    repr(field.default)
                    if field.default is not dataclasses.MISSING
                    else "factory"
                    if field.default_factory is not dataclasses.MISSING
                    else None
                ),
            }
            for field in dataclasses.fields(value)
        ]
    return description


def public_api() -> dict[str, Any]:
    """Describe ``pyworldatlas`` and ``pyworldatlas.models`` exports."""
    import pyworldatlas
    import pyworldatlas.models as models

    model_names = sorted(
        name
        for name, value in vars(models).items()
        if not name.startswith("_") and isinstance(value, type)
        and value.__module__.startswith("pyworldatlas.models")
    )
    return {
        "pyworldatlas.__all__": sorted(pyworldatlas.__all__),
        "pyworldatlas": {
            name: describe(getattr(pyworldatlas, name))
            for name in sorted(pyworldatlas.__all__)
            if name != "__version__"
        },
        "pyworldatlas.models": model_names,
    }
