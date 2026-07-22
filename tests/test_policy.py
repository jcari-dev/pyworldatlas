from dataclasses import fields
import json
from pathlib import Path
import unittest

from pyworldatlas import Atlas, Country


ROOT = Path(__file__).resolve().parents[1]


class EducationalPolicyTests(unittest.TestCase):
    def test_policy_is_published_in_the_repository_and_documentation(self):
        policy = (ROOT / "EDUCATIONAL_AND_NEUTRALITY_POLICY.md").read_text(
            encoding="utf-8"
        )
        conduct = (ROOT / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        docs_index = (ROOT / "docs/source/index.rst").read_text(encoding="utf-8")

        for heading in (
            "## Editorial commitments",
            "## Source-selection policy",
            "## Country names, areas, and borders",
            "## Publication boundaries",
            "## Corrections and accountability",
        ):
            self.assertIn(heading, policy)
        self.assertIn("Unacceptable participation", conduct)
        self.assertIn("EDUCATIONAL_AND_NEUTRALITY_POLICY.md", readme)
        self.assertIn("educational_principles", docs_index)

    def test_country_profile_has_no_unused_classification(self):
        with Atlas() as atlas:
            self.assertTrue(all(not hasattr(country, "status") for country in atlas))

    def test_country_profile_contains_only_reviewed_fields(self):
        self.assertEqual(
            {field.name for field in fields(Country)},
            {
                "aliases",
                "anthems",
                "calling_codes",
                "capitals",
                "codes",
                "currency",
                "demonyms",
                "flag",
                "formal_name",
                "geography",
                "languages",
                "local_names",
                "major_cities",
                "mottos",
                "name",
                "names",
                "observed_timezones",
                "official_name",
                "population",
                "postal_code",
                "sources",
                "timezones",
                "top_level_domain",
            },
        )

    def test_every_runtime_source_has_a_declared_field_role(self):
        matrix = json.loads(
            (ROOT / "pipeline/config/field_sources.json").read_text(encoding="utf-8")
        )
        declared_sources = {
            source_id for source_ids in matrix.values() for source_id in source_ids
        }
        with Atlas() as atlas:
            runtime_sources = {
                source.id: source
                for country in atlas
                for source in country.sources
            }
        self.assertEqual(set(runtime_sources), declared_sources)
        self.assertTrue(
            all(
                source.name
                and source.homepage.startswith("https://")
                and source.retrieved_at
                for source in runtime_sources.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
