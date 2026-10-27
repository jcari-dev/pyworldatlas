"""Place files, the local place index, and the place search API."""

from __future__ import annotations

from pathlib import Path
import random
import sqlite3
import tempfile
import unittest

from pyworldatlas import Atlas, Coordinate, Country, Place, PlaceDistance, PlaceNotFoundError
from pyworldatlas import _placefile
from pyworldatlas._placefile import PlaceFileError, PlaceRecord

ROOT = Path(__file__).resolve().parents[1]
SCHOOL_ATLAS = ROOT / "src/pyworldatlas/data/places.pwpl"


def sample_records(count: int = 3_000, seed: int = 7) -> list[PlaceRecord]:
    """Synthetic places spread over the globe, including the poles and the date line."""
    rng = random.Random(seed)
    records = [
        PlaceRecord("Lago Azul", "Blue Lake", "H.LK", "PE", -15.8, -69.4, None, 3812, 90),
        PlaceRecord("Ville", "Ville", "P.PPL", "FR", 48.85, 2.35, 2_100_000, None, 200),
        PlaceRecord("Ville", "Ville", "P.PPL", "CA", 45.5, -73.6, 800, None, 3),
        PlaceRecord("East Edge", "East Edge", "T.ISL", "FJ", -17.0, 179.99, None, None, 1),
        PlaceRecord("West Edge", "West Edge", "T.ISL", "WS", -17.0, -179.99, None, -5, 1),
        PlaceRecord("North Pole", "North Pole", "L.AREA", "", 90.0, 0.0, None, 0, 50),
        PlaceRecord("Łódź", "Lodz", "P.PPLA", "PL", 51.77, 19.46, 670_000, 200, 120),
    ]
    for number in range(count):
        records.append(PlaceRecord(
            f"Place {number}", f"Place {number}", rng.choice(["P.PPL", "T.MT", "H.STM", "S.CSTL"]),
            rng.choice(["US", "BR", "JP", "KE"]),
            round(rng.uniform(-89.9, 89.9), 3), round(rng.uniform(-179.9, 179.9), 3),
            rng.choice([None, rng.randrange(1, 10_000_000)]), rng.choice([None, rng.randrange(-400, 8_000)]),
            rng.randrange(0, 256),
        ))
    records.sort(key=lambda record: _placefile.hilbert_key(record.latitude, record.longitude))
    return records


class PlaceFileTests(unittest.TestCase):
    def test_round_trip_keeps_every_field(self) -> None:
        records = sample_records(500)
        data = _placefile.encode(records, precision=1_000, meta={"edition": "test"})
        decoded = list(_placefile.decode(data))
        self.assertEqual(len(decoded), len(records))
        for original, copy in zip(records, decoded, strict=True):
            self.assertEqual(
                (copy.name, copy.english, copy.code, copy.country, copy.population, copy.elevation_m, copy.fame),
                (original.name, original.english, original.code, original.country,
                 original.population, original.elevation_m, original.fame),
            )
            self.assertAlmostEqual(copy.latitude, original.latitude, places=3)
            self.assertAlmostEqual(copy.longitude, original.longitude, places=3)
        self.assertEqual(_placefile.read_header(data)["meta"], {"edition": "test"})

    def test_encoding_is_reproducible_and_small(self) -> None:
        records = sample_records(2_000)
        first = _placefile.encode(records, precision=1_000, meta={})
        self.assertEqual(first, _placefile.encode(records, precision=1_000, meta={}))
        self.assertLess(len(first) / len(records), 30)

    def test_damaged_files_are_refused(self) -> None:
        with self.assertRaises(PlaceFileError):
            _placefile.read_header(b"nope")
        data = _placefile.encode(sample_records(10), precision=1_000, meta={})
        with self.assertRaises(PlaceFileError):
            _placefile.read_header(data[:4] + b"\x02\x00\x00\x00{}")
        with self.assertRaises(PlaceFileError):
            list(_placefile.decode(data[:-20]))


class PlaceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = sample_records()
        cls.data = _placefile.encode(cls.records, precision=1_000, meta={})
        cls.index = sqlite3.connect(":memory:")
        _placefile.build_index(cls.data, cls.index)
        cls.index.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.index.close()

    def test_find_matches_local_and_english_names_without_accents(self) -> None:
        self.assertEqual([row["name"] for _, row in _placefile.find(self.index, "blue lake", 5)], ["Lago Azul"])
        self.assertEqual([row["name"] for _, row in _placefile.find(self.index, "LODZ", 5)], ["Łódź"])
        scores = {row["country"]: score for score, row in _placefile.find(self.index, "ville", 5)}
        self.assertEqual(scores, {"FR": 2, "CA": 2})
        prefix = _placefile.find(self.index, "place 12", 50)
        self.assertTrue(prefix and all(score == 1 for score, _ in prefix[1:]))
        self.assertEqual(_placefile.find(self.index, "!!!", 5), [])

    def test_near_is_exact_everywhere(self) -> None:
        rng = random.Random(3)
        decoded = list(_placefile.decode(self.data))
        points = [(-17.0, 179.95), (-17.0, -179.95), (89.95, 120.0), (-89.9, 0.0), (0.0, 0.0)]
        points += [(rng.uniform(-90, 90), rng.uniform(-180, 180)) for _ in range(300)]
        for lat, lon in points:
            expected = sorted(
                _placefile.distance_km(lat, lon, record.latitude, record.longitude) for record in decoded
            )[:7]
            found = [distance for distance, _ in _placefile.near([self.index], lat, lon, 7)]
            for want, got in zip(expected, found, strict=True):
                self.assertAlmostEqual(want, got, places=6, msg=(lat, lon))

    def test_index_is_cached_once_and_falls_back_to_memory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "places.pwpl"
            source.write_bytes(self.data)
            cache = Path(folder) / "cache"
            first = _placefile.open_index(source, cache)
            built = list(cache.glob("places-*.sqlite3"))
            second = _placefile.open_index(source, cache)
            self.assertEqual(len(built), 1)
            self.assertEqual(list(cache.glob("places-*.sqlite3")), built)
            memory = _placefile.open_index(source, None)
            for connection in (first, second, memory):
                self.assertEqual(connection.execute("SELECT count(*) FROM place").fetchone()[0], len(self.records))
                connection.close()
            blocked = Path(folder) / "file-not-folder"
            blocked.write_text("x")
            fallback = _placefile.open_index(source, blocked / "cache")
            self.assertEqual(fallback.execute("SELECT count(*) FROM place").fetchone()[0], len(self.records))
            fallback.close()


@unittest.skipUnless(SCHOOL_ATLAS.is_file(), "school atlas not built")
class PlaceSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.folder = tempfile.TemporaryDirectory()
        cls.atlas = Atlas(data_dir=cls.folder.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()
        cls.folder.cleanup()

    def test_famous_places_come_first(self) -> None:
        kilimanjaro = self.atlas.place("Kilimanjaro")
        self.assertEqual((kilimanjaro.kind, kilimanjaro.country_code), ("mountain", "TZ"))
        victoria = self.atlas.place("Lake Victoria")
        self.assertEqual(victoria.category, "water")
        self.assertLess(abs(victoria.coordinates.latitude), 5)
        self.assertEqual(self.atlas.place("Mount Fuji").country_code, "JP")

    def test_english_names_find_local_names(self) -> None:
        titicaca = self.atlas.place("Lake Titicaca")
        self.assertEqual(titicaca.english_name, "Lake Titicaca")
        self.assertNotEqual(titicaca.name, titicaca.english_name)
        self.assertIn("lake", str(titicaca))

    def test_search_filters(self) -> None:
        volcanoes = self.atlas.search_places("Fuji", kind="volcano")
        self.assertTrue(volcanoes and all(place.kind == "volcano" for place in volcanoes))
        french = self.atlas.search_places("Paris", country="France", limit=3)
        self.assertTrue(french and all(place.country_code == "FR" for place in french))
        water = self.atlas.search_places("Victoria", category="water", limit=5)
        self.assertTrue(water and all(place.category == "water" for place in water))
        self.assertIn("volcano", self.atlas.place_kinds())
        self.assertIn("landform", self.atlas.place_categories())

    def test_places_near(self) -> None:
        results = self.atlas.places_near((48.8584, 2.2945), limit=5)
        self.assertEqual(len(results), 5)
        self.assertTrue(all(isinstance(item, PlaceDistance) for item in results))
        distances = [item.distance for item in results]
        self.assertEqual(distances, sorted(distances))
        self.assertLess(distances[-1], 10)
        lakes = self.atlas.places_near(Coordinate(-1.0, 33.0), category="water", limit=3, unit="mi")
        self.assertTrue(lakes and all(item.unit == "mi" and item.place.category == "water" for item in lakes))
        origin = self.atlas.place("Mount Fuji")
        nearby = self.atlas.places_near(origin, limit=3)
        self.assertTrue(all(item.distance > 0 for item in nearby))
        self.assertIn("place", nearby[0].to_dict())

    def test_places_in_a_country(self) -> None:
        peru = self.atlas.places_in("Peru", category="landmark", limit=5)
        self.assertIn("Machu Picchu", [place.english_name for place in peru])
        self.assertTrue(all(place.country_code == "PE" for place in peru))
        fame = [place.fame for place in self.atlas.places_in("JP", limit=10)]
        self.assertEqual(fame, sorted(fame, reverse=True))
        volcanoes = self.atlas.places_in("Iceland", kind="volcano", limit=3)
        self.assertTrue(volcanoes and all(place.kind == "volcano" for place in volcanoes))
        with self.assertRaises(ValueError):
            self.atlas.places_in("Peru", limit=0)

    def test_lookup_finds_anything(self) -> None:
        georgia = self.atlas.lookup("Georgia", limit=3)
        self.assertIsInstance(georgia[0], Country)
        self.assertEqual(georgia[0].alpha2, "GE")
        self.assertIsInstance(georgia[1], Place)
        self.assertEqual(georgia[1].country_code, "US")
        self.assertEqual([str(item) for item in self.atlas.lookup("JP")], ["Japan"])
        everest = self.atlas.lookup("Everest", limit=1)[0]
        self.assertIsInstance(everest, Place)
        self.assertEqual(everest.english_name, "Mount Everest")
        # A country found among places appears once, as its full profile.
        ireland = self.atlas.lookup("Ireland")
        self.assertEqual(sum(isinstance(item, Country) for item in ireland), 1)
        self.assertEqual(self.atlas.lookup("Zzyzx Qwertyland"), ())
        with self.assertRaises(ValueError):
            self.atlas.lookup("Paris", limit=0)

    def test_bad_input(self) -> None:
        with self.assertRaises(PlaceNotFoundError):
            self.atlas.place("Zzyzx Qwertyland")
        with self.assertRaises(ValueError):
            self.atlas.search_places("Paris", kind="spaceport")
        with self.assertRaises(ValueError):
            self.atlas.search_places("Paris", category="sky")
        with self.assertRaises(ValueError):
            self.atlas.search_places("   ")
        with self.assertRaises(ValueError):
            self.atlas.search_places("Paris", limit=0)
        with self.assertRaises(TypeError):
            self.atlas.search_places(5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            self.atlas.places_near((0, 0), unit="furlongs")
        with self.assertRaises(ValueError):
            self.atlas.places_near((0, 0), limit=True)

    def test_place_model(self) -> None:
        place = self.atlas.place("Kilimanjaro")
        self.assertIsInstance(place, Place)
        self.assertIsNotNone(place.elevation_m)
        self.assertEqual(place.feature_code[:1], "T")


if __name__ == "__main__":
    unittest.main()
