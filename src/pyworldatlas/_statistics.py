"""Read the optional statistics pack: World Bank indicators by country and year."""

from __future__ import annotations

import json
import lzma
from pathlib import Path

from .models import Indicator

FILE = "statistics.json.xz"


class Statistics:
    """Indicators and yearly values decoded from one pack file."""

    def __init__(self, path: Path) -> None:
        document = json.loads(lzma.decompress(path.read_bytes()))
        self.snapshot: str = document["snapshot"]
        self.indicators = {
            key: Indicator(key, item["name"], item["unit"], item["code"], item["source"], item["decimals"])
            for key, item in sorted(document["indicators"].items())
        }
        self.series: dict[str, dict[str, tuple[int, tuple[float | None, ...]]]] = {
            key: {area: (first, tuple(values)) for area, (first, values) in by_area.items()}
            for key, by_area in document["series"].items()
        }
