from hashlib import sha256
from pathlib import Path
import unittest

from pyworldatlas_builder.core import (
    EXPECTED_CAPITAL_COUNT,
    EXPECTED_CITY_COUNT,
    EXPECTED_COUNTRY_COUNT,
    build_database,
    normalize,
    parse_un_m49,
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
        self.assertTrue(all(record["source_id"] for rows in records.values() for record in rows))
        self.assertTrue(all(-90 <= c["data"]["latitude"] <= 90 and -180 <= c["data"]["longitude"] <= 180 for c in records["cities"]))

    def test_database_build_is_reproducible(self):
        write_manifests(ROOT)
        records = normalize(ROOT)
        first = sha256(build_database(ROOT, records).read_bytes()).hexdigest()
        second = sha256(build_database(ROOT, records).read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
