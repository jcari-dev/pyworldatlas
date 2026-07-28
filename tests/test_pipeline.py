from hashlib import sha256
import json
from pathlib import Path
import unittest

from pyworldatlas_builder.core import (
    EXPECTED_ANTHEM_COUNT,
    EXPECTED_BORDER_COUNT,
    EXPECTED_CAPITAL_COUNT,
    EXPECTED_CITY_COUNT,
    EXPECTED_COUNTRY_COUNT,
    EXPECTED_DEMONYM_COUNT,
    EXPECTED_ENGLISH_FORMAL_NAME_COUNT,
    EXPECTED_LOCAL_NAME_COUNT,
    EXPECTED_MOTTO_COUNT,
    EXPECTED_PHYSICAL_PROFILE_COUNT,
    EXPECTED_RIVER_COUNT,
    EXPECTED_LAKE_COUNT,
    EXPECTED_KOPPEN_PROFILE_COUNT,
    EXPECTED_KOPPEN_GAPS,
    EXPECTED_TIMEZONE_COUNTRY_COUNT,
    build_database,
    normalize,
    parse_un_m49,
    parse_country_local_names,
    parse_english_formal_names,
    parse_factbook_physical_geography,
    parse_koppen_climate_profiles,
    write_manifests,
)


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_un_snapshot_contains_exact_scope(self):
        records = parse_un_m49(ROOT)
        self.assertEqual(len(records), EXPECTED_COUNTRY_COUNT)
        self.assertIn("AD", records)
        self.assertIn("ZW", records)

    def test_normalized_records_are_sourced(self):
        records = normalize(ROOT)
        self.assertEqual(len(records["countries"]), EXPECTED_COUNTRY_COUNT)
        self.assertEqual(len(records["capitals"]), EXPECTED_CAPITAL_COUNT)
        self.assertEqual(len(records["cities"]), EXPECTED_CITY_COUNT)
        self.assertEqual(len(records["local_names"]), EXPECTED_LOCAL_NAME_COUNT)
        self.assertEqual(
            len(records["formal_names"]), EXPECTED_ENGLISH_FORMAL_NAME_COUNT
        )
        self.assertEqual(len(records["borders"]), EXPECTED_BORDER_COUNT)
        self.assertEqual(len(records["anthems"]), EXPECTED_ANTHEM_COUNT)
        self.assertEqual(len(records["mottos"]), EXPECTED_MOTTO_COUNT)
        self.assertEqual(len(records["demonyms"]), EXPECTED_DEMONYM_COUNT)
        self.assertEqual(
            len(records["physical_profiles"]), EXPECTED_PHYSICAL_PROFILE_COUNT
        )
        self.assertEqual(
            len(records["climate_profiles"]), EXPECTED_KOPPEN_PROFILE_COUNT
        )
        self.assertEqual(
            len({record["country_code"] for record in records["timezones"]}),
            EXPECTED_TIMEZONE_COUNTRY_COUNT,
        )
        self.assertEqual(len(records["language_profiles"]), 722)
        self.assertTrue(all(record["data"]["population"] is None or record["data"]["population"] >= 0 for record in records["countries"]))
        self.assertTrue(all(isinstance(record["data"]["calling_codes"], list) for record in records["countries"]))
        self.assertTrue(all(isinstance(record["data"]["language_codes"], list) for record in records["countries"]))
        self.assertTrue(all(record["source_id"] for rows in records.values() for record in rows))
        self.assertTrue(all(-90 <= c["data"]["latitude"] <= 90 and -180 <= c["data"]["longitude"] <= 180 for c in records["cities"]))

    def test_reviewed_border_graph_is_canonical(self):
        records = normalize(ROOT)
        edges = {
            (record["country_code"], record["neighbor_code"])
            for record in records["borders"]
        }
        self.assertEqual(len(edges), EXPECTED_BORDER_COUNT)
        self.assertTrue(all(first < second for first, second in edges))
        self.assertIn(("CN", "HK"), edges)
        self.assertIn(("ES", "GI"), edges)
        self.assertNotIn(("AL", "RS"), edges)
        self.assertNotIn(("CU", "US"), edges)

    def test_country_local_name_coverage_is_complete(self):
        expected_countries = set(parse_un_m49(ROOT))
        records = parse_country_local_names(ROOT, expected_countries)
        self.assertEqual({record["country_code"] for record in records}, expected_countries)
        self.assertEqual(len(records), EXPECTED_LOCAL_NAME_COUNT)
        self.assertEqual(len({record["country_code"] for record in records}), 248)
        self.assertEqual(
            sum(record["source_id"] == "ungegn-country-names-2017" for record in records),
            10,
        )
        self.assertEqual(
            sum(record["source_id"] == "unicode-cldr-48.2" for record in records),
            238,
        )
        self.assertEqual(
            sum(record["data"]["name_kind"] == "national_official" for record in records),
            10,
        )
        self.assertTrue(
            {"Arab", "Cyrl", "Deva", "Hans", "Jpan", "Latn"}
            <= {record["data"]["script_code"] for record in records}
        )
        self.assertEqual(
            sum(record["data"]["is_official_language"] for record in records),
            244,
        )
        locators = {record["country_code"]: record["source_record_id"] for record in records}
        self.assertIn("PDF page 17 (printed page 16)", locators["BR"])
        self.assertIn("PDF page 92 (printed page 91)", locators["CH"])
        self.assertIn("PDF page 30 (printed page 29)", locators["DO"])
        self.assertIn("PDF page 48 (printed page 47)", locators["JP"])
        self.assertIn("common/main/ca.xml", locators["AD"])
        self.assertIn("supplementalData.xml", locators["AE"])
        self.assertEqual(
            sha256((ROOT / "build_data/raw/ungegn-country-names/2017-07-17/E_CONF.105_13_CRP.13-EN.pdf").read_bytes()).hexdigest(),
            "a74510091e6720d6fe505a4c7d6d2ce1b18a0527f0cfd8318cb99cce16b65d1c",
        )
        cldr_path = ROOT / "build_data/raw/unicode-cldr/48.2/country_identity.json"
        self.assertEqual(
            sha256(cldr_path.read_bytes()).hexdigest(),
            "033e6b58bf52d0a46f4720fe1d259c9e8ba1ae92e524841bd918c1956c84b252",
        )
        cldr = json.loads(cldr_path.read_text(encoding="utf-8"))
        self.assertEqual(cldr["license_name"], "Unicode License v3")
        self.assertEqual(len(cldr["records"]), 248)

    def test_english_formal_name_layer_is_reviewed_and_current(self):
        expected_countries = set(parse_un_m49(ROOT))
        records = parse_english_formal_names(ROOT, expected_countries)
        by_country = {record["country_code"]: record for record in records}

        self.assertEqual(len(records), EXPECTED_ENGLISH_FORMAL_NAME_COUNT)
        self.assertEqual(
            sum(
                record["data"]["formal_name_status"] == "source_provided"
                for record in records
            ),
            195,
        )
        self.assertEqual(
            sum(
                record["data"]["formal_name_status"] == "same_as_short"
                for record in records
            ),
            45,
        )
        self.assertEqual(by_country["TR"]["data"]["formal_name"], "Republic of Türkiye")
        self.assertEqual(
            by_country["GY"]["data"]["formal_name"],
            "Co-operative Republic of Guyana",
        )
        self.assertEqual(
            by_country["VN"]["data"]["formal_name"],
            "Socialist Republic of Viet Nam",
        )
        self.assertEqual(by_country["JP"]["data"]["formal_name"], "Japan")
        self.assertEqual(by_country["JP"]["data"]["formal_name_status"], "same_as_short")
        self.assertEqual(
            expected_countries - set(by_country),
            {"AX", "BQ", "GF", "GP", "MQ", "RE", "UM", "YT"},
        )
        factbook_path = ROOT / "build_data/raw/cia-world-factbook/2025/country_identity.json"
        self.assertEqual(
            sha256(factbook_path.read_bytes()).hexdigest(),
            "e5d9778a6beb946d4b179985cac7e06e00f020ee6d686b542d5431e18be45cfe",
        )
        wikidata_path = ROOT / "build_data/raw/wikidata/2026-07-21/official-names.json"
        self.assertEqual(
            sha256(wikidata_path.read_bytes()).hexdigest(),
            "841f3d5ae07f18469dc302e326954484d6cf812ee5bbbb07ff63f2edec2e85fe",
        )

    def test_reference_snapshots_are_pinned_and_complete(self):
        expected_hashes = {
            "build_data/raw/unicode-cldr/48.2/country_reference.json":
                "5e48a1c193b64fb02941ea8c369a92a965618da7a532ec3bd1fe82b452badd79",
            "build_data/raw/iana/2026-07-22/language-subtag-registry.txt":
                "be1fad86a99e3a932d07b80c9b3c271ec2381a5909ce22420144e5077ab0a43a",
            "build_data/raw/geonames/2026-07-22/timeZones.txt":
                "ea6f8bdcc259c21c562e8f7e7e0b0457cb89403bed60c76aac49ccee9a9ed18c",
            "build_data/raw/wikidata/2026-07-22/national-mottos.json":
                "4af587a6f19febd169b99850669ecdc426ac2b86ef5399e3eab2f5e51d3e448c",
            "build_data/raw/koppen-geiger/2023/1991_2020/koppen_geiger_0p1.tif":
                "d03ae67c66b48bc423bb5ebdda2a9a735262e26972576e2bb6a6881dc4e02bf4",
            "build_data/raw/koppen-geiger/2023/legend.txt":
                "6373d6b522b7b27ec9afbf51dc477a8a9d269074321d51d8e047c23691d67fcb",
            "build_data/raw/koppen-geiger/2023/country_zones.json":
                "bc59a51670cb6e9ba7953cc910b238aa08b5706ff99cecaa92cc77be735a0137",
            "build_data/raw/etopo-2022/2026-07-28/etopo-2022-5arcmin.nc":
                "fe35017f8cf4d77dbb00677a99d6b96a0e235fac295b52029174943d3d9afe9a",
            "build_data/raw/natural-earth/2026-07-21/ne_50m_rivers_lake_centerlines.zip":
                "c607d9d7e7702827a7996fff6dc17b87a338c5ed3b52d12c402e0c9669cc7b56",
            "build_data/raw/natural-earth/2026-07-28/ne_10m_admin_0_map_units.zip":
                "45bebe2aaf8bf42b9daf4428594925bcb11eabd32fe9dc6e0acf681438053eb5",
            "build_data/raw/natural-earth/2026-07-28/ne_10m_rivers_lake_centerlines.zip":
                "ded71b01870855ccfe19b51f2ec14c9bb48fae23c0e9f3c11974d426433b5c38",
        }
        for relative_path, expected_hash in expected_hashes.items():
            self.assertEqual(
                sha256((ROOT / relative_path).read_bytes()).hexdigest(),
                expected_hash,
            )

        records = normalize(ROOT)
        self.assertEqual(
            {record["country_code"] for record in records["countries"]}
            - {record["country_code"] for record in records["timezones"]},
            {"BV", "HM"},
        )
        self.assertEqual(
            len({record["data"]["code"] for record in records["language_profiles"]}),
            503,
        )
        self.assertEqual(
            len({
                record["data"]["currency_code"]
                for record in records["countries"]
                if record["data"]["currency_code"]
            }),
            153,
        )

    def test_physical_and_climate_layers_are_pinned_and_complete(self):
        country_codes = set(parse_un_m49(ROOT))
        physical = parse_factbook_physical_geography(ROOT, country_codes)
        climate = parse_koppen_climate_profiles(ROOT, country_codes)

        self.assertEqual(len(physical), EXPECTED_PHYSICAL_PROFILE_COUNT)
        self.assertEqual(
            sum(len(record["data"]["rivers"]) for record in physical),
            EXPECTED_RIVER_COUNT,
        )
        self.assertEqual(
            sum(len(record["data"]["lakes"]) for record in physical),
            EXPECTED_LAKE_COUNT,
        )
        self.assertEqual(len(climate), EXPECTED_KOPPEN_PROFILE_COUNT)
        self.assertEqual(
            country_codes - {record["country_code"] for record in climate},
            EXPECTED_KOPPEN_GAPS,
        )
        self.assertTrue(
            all(
                record["data"]["zones"][0]["code"]
                == record["data"]["dominant_code"]
                for record in climate
            )
        )
        brazil = next(record for record in physical if record["country_code"] == "BR")
        self.assertEqual(brazil["data"]["highest_point"]["name"], "Pico da Neblina")
        self.assertEqual(brazil["data"]["rivers"][0]["name"], "Amazon")

    def test_database_build_is_reproducible(self):
        write_manifests(ROOT)
        records = normalize(ROOT)
        first = sha256(build_database(ROOT, records, install=False).read_bytes()).hexdigest()
        second = sha256(build_database(ROOT, records, install=False).read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
