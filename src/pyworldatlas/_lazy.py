"""Load a module the first time one of its names is used."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


class LazyModule:
    """Stand in for a module and import it on first attribute access."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._module: ModuleType | None = None

    def __getattr__(self, attribute: str) -> Any:
        if self._module is None:
            self._module = import_module(self._name)
        return getattr(self._module, attribute)
