from hashlib import sha256
from pathlib import Path
import unittest

from pyworldatlas_builder.core import TARGET_CODES, build_database, normalize, parse_un_m49, write_manifests


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_un_fixture_contains_exact_scope(self):
        self.assertEqual(set(parse_un_m49(ROOT)), set(TARGET_CODES))

    def test_normalized_records_are_sourced(self):
        records = normalize(ROOT)
        self.assertEqual(len(records["countries"]), 12)
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
