from hashlib import sha256
from pathlib import Path
import unittest

from pyworldatlas_builder.core import (
    EXPECTED_CAPITAL_COUNT,
    EXPECTED_CITY_COUNT,
    EXPECTED_COUNTRY_COUNT,
    EXPECTED_LOCAL_NAME_COUNT,
    build_database,
    normalize,
    parse_un_m49,
    parse_country_local_names,
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
        self.assertTrue(all(record["data"]["population"] is None or record["data"]["population"] >= 0 for record in records["countries"]))
        self.assertTrue(all(isinstance(record["data"]["calling_codes"], list) for record in records["countries"]))
        self.assertTrue(all(isinstance(record["data"]["language_codes"], list) for record in records["countries"]))
        self.assertTrue(all(record["source_id"] for rows in records.values() for record in rows))
        self.assertTrue(all(-90 <= c["data"]["latitude"] <= 90 and -180 <= c["data"]["longitude"] <= 180 for c in records["cities"]))

    def test_country_local_name_pilot_is_exact(self):
        records = parse_country_local_names(ROOT, {"BR", "CH"})
        self.assertEqual({record["country_code"] for record in records}, {"BR", "CH"})
        self.assertEqual(sum(record["country_code"] == "CH" for record in records), 4)
        self.assertTrue(all(record["source_id"] == "ungegn-country-names-2017" for record in records))
        locators = {record["country_code"]: record["source_record_id"] for record in records}
        self.assertIn("PDF page 17 (printed page 16)", locators["BR"])
        self.assertIn("PDF page 92 (printed page 91)", locators["CH"])
        self.assertEqual(
            sha256((ROOT / "build_data/raw/ungegn-country-names/2017-07-17/E_CONF.105_13_CRP.13-EN.pdf").read_bytes()).hexdigest(),
            "a74510091e6720d6fe505a4c7d6d2ce1b18a0527f0cfd8318cb99cce16b65d1c",
        )

    def test_database_build_is_reproducible(self):
        write_manifests(ROOT)
        records = normalize(ROOT)
        first = sha256(build_database(ROOT, records).read_bytes()).hexdigest()
        second = sha256(build_database(ROOT, records).read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
