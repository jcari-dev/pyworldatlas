"""Read the optional landmarks pack: airports and World Heritage sites."""

from __future__ import annotations

import json
import lzma
from pathlib import Path

from .models import Airport, Coordinate, WorldHeritageSite

FILE = "landmarks.json.xz"


class Landmarks:
    """Airports and World Heritage sites decoded from one pack file."""

    def __init__(self, path: Path) -> None:
        document = json.loads(lzma.decompress(path.read_bytes()))
        self.sources: dict[str, dict[str, str]] = document["sources"]
        self.airports = tuple(
            Airport(iata, icao, name, town, country, Coordinate(lat, lon), elevation, size)
            for iata, icao, name, town, country, lat, lon, elevation, size in document["airports"]
        )
        self.world_heritage = tuple(
            WorldHeritageSite(
                number, name,
                Coordinate(lat, lon) if lat is not None and lon is not None else None,
                year, category,
            )
            for number, name, lat, lon, year, category in document["world_heritage"]
        )
        self.by_code = {airport.iata_code: airport for airport in self.airports}
        self.by_code.update({airport.icao_code: airport for airport in self.airports if airport.icao_code})
