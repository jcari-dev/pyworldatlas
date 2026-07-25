from dataclasses import fields
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import re
import unittest

from pyworldatlas import Atlas, Country, __version__


ROOT = Path(__file__).resolve().parents[1]


class EducationalPolicyTests(unittest.TestCase):
    def test_browser_playground_is_versioned_and_published(self):
        playground = (ROOT / "docs/source/playground.rst").read_text(
            encoding="utf-8"
        )
        docs_index = (ROOT / "docs/source/index.rst").read_text(encoding="utf-8")
        docs_config = (ROOT / "docs/source/conf.py").read_text(encoding="utf-8")
        recipes = (ROOT / "docs/source/recipes.rst").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        worker = (ROOT / "docs/source/_static/playground-worker.mjs").read_text(
            encoding="utf-8"
        )
        interface = (ROOT / "docs/source/_static/playground.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            f'data-package="pyworldatlas=={__version__}"',
            playground,
        )
        self.assertIn("playground", docs_index)
        self.assertIn("recipes", docs_index)
        self.assertIn("/playground.html", readme)
        self.assertIn("/recipes.html", readme)
        self.assertIn("micropip.install", worker)
        self.assertIn("import(`${provider.moduleBase}pyodide.mjs`)", worker)
        self.assertIn("https://unpkg.com/pyodide@", worker)
        self.assertIn("https://cdn.jsdelivr.net/pyodide/", worker)
        self.assertIn('const PYODIDE_VERSION = "314.0.3"', worker)
        self.assertNotIn("import { loadPyodide }", worker)
        initialize = worker[worker.index("async function initialize") :]
        self.assertLess(
            initialize.index("Starting the browser Python worker"),
            initialize.index("loadBrowserPython()"),
        )
        self.assertIn("new Worker", interface)
        self.assertIn('{"defer": "defer"}', docs_config)
        self.assertIn("Python startup timed out", interface)
        self.assertIn("within 45 seconds", interface)

        preset_ids = re.findall(r'\n\s+id: "([^"]+)"', interface)
        recipe_links = re.findall(r"playground\.html#recipe=([a-z-]+)", recipes)
        self.assertEqual(len(preset_ids), 14)
        self.assertEqual(len(set(preset_ids)), 14)
        self.assertTrue(set(recipe_links).issubset(preset_ids))

    def test_browser_playground_examples_execute(self):
        interface = (ROOT / "docs/source/_static/playground.js").read_text(
            encoding="utf-8"
        )
        examples = re.findall(
            r"code: `(.+?)`,\n\s+},",
            interface,
            flags=re.DOTALL,
        )

        self.assertEqual(len(examples), 14)
        for number, example in enumerate(examples, 1):
            with self.subTest(example=number), redirect_stdout(StringIO()):
                exec(
                    compile(example, f"<browser-playground-{number}>", "exec"),
                    {},
                )

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
