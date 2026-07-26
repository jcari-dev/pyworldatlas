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
    def test_documentation_discovery_metadata_is_published(self):
        docs_config = (ROOT / "docs/source/conf.py").read_text(encoding="utf-8")
        layout = (ROOT / "docs/source/_templates/layout.html").read_text(
            encoding="utf-8"
        )
        robots = (ROOT / "docs/source/robots.txt").read_text(encoding="utf-8")

        self.assertIn("html_baseurl", docs_config)
        self.assertIn('html_favicon = "_static/globe.svg"', docs_config)
        self.assertIn('templates_path = ["_templates"]', docs_config)
        self.assertIn('app.connect("html-page-context", _set_page_url)', docs_config)
        self.assertIn('app.connect("build-finished", _write_sitemap)', docs_config)
        self.assertIn("| PyWorldAtlas</title>", layout)
        self.assertNotIn("&mdash;", layout)
        self.assertIn('name="description"', layout)
        self.assertIn('property="og:title"', layout)
        self.assertIn('type="application/ld+json"', layout)
        self.assertIn("/sitemap.xml", robots)
        self.assertTrue((ROOT / "docs/source/_static/globe.svg").is_file())

    def test_changelog_release_headings_do_not_include_dates(self):
        dated_heading = r"(?m)^(?:## )?\d+\.\d+\.\d+.*\b20\d{2}-\d{2}-\d{2}\b"
        for path in (ROOT / "CHANGELOG.md", ROOT / "docs/source/changelog.rst"):
            with self.subTest(path=path):
                self.assertNotRegex(path.read_text(encoding="utf-8"), dated_heading)

    def test_repository_presentation_is_current(self):
        obsolete = {
            "MIGRATION_FROM_0.0.md",
            "MILESTONE_0_1_REPORT.md",
            "RELEASE_0_2_STATUS.md",
            "RELEASE_0_3_STATUS.md",
            "RELEASE_0_3_1_STATUS.md",
            "RELEASE_0_4_STATUS.md",
            "RELEASE_0_5_STATUS.md",
            "RELEASE_0_6_STATUS.md",
            "RELEASE_0_7_STATUS.md",
        }
        self.assertFalse(any((ROOT / name).exists() for name in obsolete))

        references = {
            "BOUNDARIES_AND_DISPUTES.md",
            "COUNTRY_IDENTITY_DATA_SPEC.md",
            "DATA_MODEL.md",
            "DATA_QUALITY.md",
            "DATA_SOURCES.md",
            "EDUCATIONAL_AND_NEUTRALITY_POLICY.md",
            "RELEASING.md",
            "ROADMAP_STATUS.md",
        }
        for name in references:
            self.assertFalse((ROOT / name).exists(), name)
            self.assertTrue((ROOT / "docs/project" / name).is_file(), name)

        for stem in (
            "baseline_0_2_0",
            "country_discovery_pilot_0_2_0",
            "release_candidate_0_2_0",
        ):
            self.assertFalse((ROOT / "build_data/reports" / f"{stem}.json").exists())
            self.assertFalse((ROOT / "build_data/reports" / f"{stem}.md").exists())

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        status = json.loads(
            (ROOT / "build_data/reports/status.json").read_text(encoding="utf-8")
        )

        self.assertIn("browser playground", readme)
        self.assertIn("classrooms", readme)
        self.assertIn("0.8 — Education and usability", roadmap)
        self.assertIn("not scheduled for 0.8", roadmap)
        self.assertEqual(status["milestones"][-3]["name"], "8 — Education and usability")

        for path in (
            "SECURITY.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/data_correction.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

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
        self.assertIn('sys.platform == "emscripten"', worker)
        self.assertIn('kwargs["uri"] = False', worker)
        self.assertIn("Preparing browser-safe dataset access", worker)
        self.assertIn("json.dumps(_details)", worker)
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

    def test_documentation_has_one_primary_onboarding_path(self):
        docs_index = (ROOT / "docs/source/index.rst").read_text(encoding="utf-8")
        start_here = docs_index.split(":caption: Start here", 1)[1].split(
            ".. toctree::", 1
        )[0]
        redirect = (ROOT / "docs/source/explore.html").read_text(encoding="utf-8")
        docs_config = (ROOT / "docs/source/conf.py").read_text(encoding="utf-8")

        self.assertEqual(
            [
                line.strip()
                for line in start_here.splitlines()
                if line.startswith("   ") and line.strip()
            ],
            ["quickstart", "playground", "installation"],
        )
        self.assertFalse((ROOT / "docs/source/explore.rst").exists())
        self.assertIn("url=quickstart.html", redirect)
        self.assertIn(
            'html_extra_path = ["robots.txt", "explore.html"]', docs_config
        )

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
        policy = (
            ROOT / "docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md"
        ).read_text(
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
        self.assertIn(
            "docs/project/EDUCATIONAL_AND_NEUTRALITY_POLICY.md", readme
        )
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
