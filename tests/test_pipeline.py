from hashlib import sha256
import json
from pathlib import Path
import unittest

from pyworldatlas_builder.core import (
    EXPECTED_BORDER_COUNT,
    EXPECTED_CAPITAL_COUNT,
    EXPECTED_CITY_COUNT,
    EXPECTED_COUNTRY_COUNT,
    EXPECTED_ENGLISH_FORMAL_NAME_COUNT,
    EXPECTED_LOCAL_NAME_COUNT,
    build_database,
    normalize,
    parse_un_m49,
    parse_country_local_names,
    parse_english_formal_names,
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
            "7127b6a1e653b93984fd821236ab408377b8b43e135de2b4b60a47974460e77c",
        )
        wikidata_path = ROOT / "build_data/raw/wikidata/2026-07-21/official-names.json"
        self.assertEqual(
            sha256(wikidata_path.read_bytes()).hexdigest(),
            "841f3d5ae07f18469dc302e326954484d6cf812ee5bbbb07ff63f2edec2e85fe",
        )

    def test_database_build_is_reproducible(self):
        write_manifests(ROOT)
        records = normalize(ROOT)
        first = sha256(build_database(ROOT, records, install=False).read_bytes()).hexdigest()
        second = sha256(build_database(ROOT, records, install=False).read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
