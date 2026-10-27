from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape


project = "PyWorldAtlas"
author = "PyWorldAtlas maintainers"
copyright = "2026, PyWorldAtlas maintainers"
release = "0.9.5"
version = "0.9"
extensions = [
    "sphinx.ext.autodoc", "sphinx.ext.autosummary", "sphinx.ext.napoleon",
    "sphinx.ext.doctest", "sphinx.ext.viewcode", "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
]
autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_class_signature = "separated"
autodoc_typehints_format = "short"
python_use_unqualified_type_names = True
nitpicky = True
nitpick_ignore = [("py:class", "pathlib.Path")]
html_theme = "sphinx_rtd_theme"
pygments_style = "friendly"
html_title = "PyWorldAtlas 0.9.5"
html_short_title = "PyWorldAtlas"
html_baseurl = "https://jcari-dev.github.io/pyworldatlas-documentation/"
html_favicon = "_static/globe.svg"
templates_path = ["_templates"]
html_theme_options = {
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}
html_context = {
    "display_github": False,
    "current_version": release,
    "site_url": html_baseurl,
    "seo_description": (
        "Explore 248 country profiles, optional 3D maps, physical geography, "
        "cities, distances, and learning tools offline with PyWorldAtlas."
    ),
}
html_static_path = ["_static"]
html_extra_path = ["robots.txt", "explore.html", ".gitignore"]
html_css_files = ["pyworldatlas.css"]
html_js_files = [("playground.js", {"defer": "defer"})]
rst_prolog = """
.. role:: atlas-flag
   :class: atlas-flag

.. role:: atlas-kicker
   :class: atlas-kicker

.. role:: atlas-example-label
   :class: atlas-example-label

.. |flag-br| image:: /_static/twemoji/1f1e7-1f1f7.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: Brazil flag emoji

.. |flag-jp| image:: /_static/twemoji/1f1ef-1f1f5.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: Japan flag emoji

.. |flag-ch| image:: /_static/twemoji/1f1e8-1f1ed.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: Switzerland flag emoji

.. |flag-cn| image:: /_static/twemoji/1f1e8-1f1f3.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: China flag emoji

.. |flag-fr| image:: /_static/twemoji/1f1eb-1f1f7.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: France flag emoji

.. |flag-ae| image:: /_static/twemoji/1f1e6-1f1ea.svg
   :class: atlas-flag-image
   :width: 1.45em
   :alt: United Arab Emirates flag emoji
"""
exclude_patterns = ["_build"]


def _write_sitemap(app, exception):
    """Write a sitemap containing every successfully built documentation page."""

    if exception is not None or app.builder.name != "html":
        return

    urls = [
        html_baseurl
        if docname == "index"
        else urljoin(html_baseurl, app.builder.get_target_uri(docname))
        for docname in sorted(app.env.found_docs)
    ]
    entries = "\n".join(f"  <url><loc>{escape(url)}</loc></url>" for url in urls)
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    Path(app.outdir, "sitemap.xml").write_text(sitemap, encoding="utf-8")


LLMS_SECTIONS = (
    ("Start here", ("quickstart", "playground", "installation")),
    ("Examples and learning", ("learning", "recipes")),
    (
        "Explore the atlas",
        (
            "country_profile", "maps", "physical_geography", "reference_facts",
            "rankings", "local_names", "capitals_cities", "coordinates_distances",
            "borders", "discovery", "searching", "serialization",
        ),
    ),
    (
        "Data and trust",
        (
            "why", "educational_principles", "data_sources", "data_quality",
            "_generated/project_status", "roadmap",
        ),
    ),
    ("Reference", ("api", "migration", "changelog")),
)
LLMS_SUMMARY = (
    "PyWorldAtlas is an offline world-geography Python package built around one "
    "bundled, source-aware database: country profiles, names, capitals, cities, "
    "physical geography, climate classes, reviewed land borders, distances, "
    "rankings, learning tools, and optional 3D maps. It has no core runtime "
    "dependencies, needs no API key, and never uses the network at runtime."
)


def _first_paragraph(doctree):
    """Return the first prose paragraph of a page as one line of text."""

    from docutils import nodes

    for paragraph in doctree.findall(nodes.paragraph):
        if isinstance(paragraph.parent, (nodes.section, nodes.document)):
            text = " ".join(paragraph.astext().split())
            if text:
                return text
    return ""


def _plain_text(app, docname):
    """Render one resolved page as plain text without raw HTML fragments."""

    from docutils import nodes

    doctree = app.env.get_and_resolve_doctree(docname, app.builder)
    for raw in list(doctree.findall(nodes.raw)):
        raw.parent.remove(raw)
    return doctree.astext().strip()


def _write_llms_files(app, exception):
    """Write the llms.txt and llms-full.txt plain-text documentation indexes."""

    if exception is not None or app.builder.name != "html":
        return

    listed = [name for _, names in LLMS_SECTIONS for name in names]
    unlisted = sorted(set(app.env.found_docs) - set(listed) - {"index"})
    missing = sorted(set(listed) - set(app.env.found_docs))
    if unlisted or missing:
        from sphinx.util import logging

        logging.getLogger(__name__).warning(
            "llms.txt sections are out of date (unlisted: %s, missing: %s)",
            ", ".join(unlisted) or "none",
            ", ".join(missing) or "none",
        )

    lines = [
        f"# PyWorldAtlas {release}",
        "",
        f"> {LLMS_SUMMARY}",
        "",
        "Install with `pip install pyworldatlas`. Every value is traced to a pinned "
        "source snapshot; missing data is `None`, never guessed. Each link below "
        "points to the plain-text source of a documentation page. The complete "
        f"documentation as one plain-text file is at {html_baseurl}llms-full.txt",
        "",
    ]
    full = [f"# PyWorldAtlas {release} documentation", "", LLMS_SUMMARY, ""]
    for section, names in LLMS_SECTIONS:
        lines.append(f"## {section}")
        lines.append("")
        for name in names:
            if name not in app.env.found_docs:
                continue
            title = app.env.titles[name].astext()
            source = urljoin(html_baseurl, f"_sources/{name}.rst.txt")
            summary = _first_paragraph(app.env.get_doctree(name))
            entry = f"- [{title}]({source})"
            lines.append(f"{entry}: {summary}" if summary else entry)
            page = urljoin(html_baseurl, app.builder.get_target_uri(name))
            full += ["", "=" * 72, f"{title}", f"Source: {page}", "=" * 72, ""]
            full.append(_plain_text(app, name))
        lines.append("")

    Path(app.outdir, "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    Path(app.outdir, "llms-full.txt").write_text(
        "\n".join(full) + "\n", encoding="utf-8"
    )


def _set_page_url(app, pagename, templatename, context, doctree):
    """Use the site root as the canonical URL for the documentation home page."""

    if pagename == "index":
        context["pageurl"] = html_baseurl


def setup(app):
    """Register small build-time additions used by the public documentation."""

    app.connect("html-page-context", _set_page_url)
    app.connect("build-finished", _write_sitemap)
    app.connect("build-finished", _write_llms_files)
