"""Airports and World Heritage sites from the landmarks pack."""

from __future__ import annotations

import tempfile
import unittest

from pack_fixtures import installed_packs

from pyworldatlas import (Airport, AmbiguousPlaceError, Atlas, PackNotInstalledError,
                          PlaceNotFoundError, SiteDistance, WorldHeritageSite)


class LandmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_airports(self) -> None:
        heathrow = self.atlas.airport("LHR")
        self.assertIsInstance(heathrow, Airport)
        self.assertEqual((heathrow.icao_code, heathrow.country_code, heathrow.size), ("EGLL", "GB", "large"))
        self.assertEqual(self.atlas.airport("egll"), heathrow)
        self.assertEqual(str(heathrow), "LHR · London Heathrow Airport (GB)")
        japan = self.atlas.airports("Japan")
        self.assertTrue(japan and all(airport.country_code == "JP" for airport in japan))
        sizes = [airport.size for airport in japan]
        self.assertEqual(sizes, sorted(sizes, key=["large", "medium", "small"].index))
        self.assertTrue(all(a.size == "large" for a in self.atlas.airports(size="large")))
        with self.assertRaises(PlaceNotFoundError):
            self.atlas.airport("ZZZ")
        with self.assertRaises(ValueError):
            self.atlas.airports(size="huge")

    def test_world_heritage_sites(self) -> None:
        sites = self.atlas.world_heritage_sites()
        self.assertGreater(len(sites), 1_200)
        self.assertEqual([site.site_id for site in sites], sorted(site.site_id for site in sites))
        machu = self.atlas.world_heritage_site("Machu Picchu")
        self.assertIsInstance(machu, WorldHeritageSite)
        self.assertEqual((machu.site_id, machu.category, machu.inscribed), (274, "mixed", 1983))
        self.assertEqual(str(machu), "Historic Sanctuary of Machu Picchu, mixed")
        self.assertEqual(self.atlas.world_heritage_site(252).name, "Taj Mahal")
        natural = self.atlas.world_heritage_sites(category="natural")
        self.assertTrue(natural and all(site.category == "natural" for site in natural))
        nearby = self.atlas.world_heritage_sites_near("Cusco", limit=3)
        self.assertTrue(all(isinstance(item, SiteDistance) for item in nearby))
        self.assertEqual([item.distance for item in nearby], sorted(item.distance for item in nearby))
        self.assertIn(274, [item.site.site_id for item in nearby])
        miles = self.atlas.world_heritage_sites_near((27.175, 78.042), limit=1, unit="mi")[0]
        self.assertEqual((miles.site.site_id, miles.unit), (252, "mi"))
        with self.assertRaises(ValueError):
            self.atlas.world_heritage_sites_near("Cusco", limit=0)
        with self.assertRaises(AmbiguousPlaceError):
            self.atlas.world_heritage_site("Historic Centre")
        with self.assertRaises(PlaceNotFoundError):
            self.atlas.world_heritage_site("Atlantis")
        with self.assertRaises(ValueError):
            self.atlas.world_heritage_sites(category="modern")

    def test_missing_pack_explains_how_to_install_it(self) -> None:
        with tempfile.TemporaryDirectory() as empty, Atlas(data_dir=empty) as atlas:
            with self.assertRaisesRegex(PackNotInstalledError, "pyworldatlas get landmarks"):
                atlas.airport("LHR")


if __name__ == "__main__":
    unittest.main()
