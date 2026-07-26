from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape


project = "PyWorldAtlas"
author = "PyWorldAtlas maintainers"
copyright = "2026, PyWorldAtlas maintainers"
release = "0.8.1"
version = "0.8"
extensions = [
    "sphinx.ext.autodoc", "sphinx.ext.autosummary", "sphinx.ext.napoleon",
    "sphinx.ext.doctest", "sphinx.ext.viewcode", "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
]
autosummary_generate = True
autodoc_member_order = "bysource"
nitpicky = True
nitpick_ignore = [("py:class", "pathlib.Path")]
html_theme = "sphinx_rtd_theme"
pygments_style = "friendly"
html_title = "PyWorldAtlas 0.8.1"
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
        "Explore 248 country profiles, cities, physical geography, distances, "
        "borders, and learning tools offline with the PyWorldAtlas Python package."
    ),
}
html_static_path = ["_static"]
html_extra_path = ["robots.txt", "explore.html"]
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


def _set_page_url(app, pagename, templatename, context, doctree):
    """Use the site root as the canonical URL for the documentation home page."""

    if pagename == "index":
        context["pageurl"] = html_baseurl


def setup(app):
    """Register small build-time additions used by the public documentation."""

    app.connect("html-page-context", _set_page_url)
    app.connect("build-finished", _write_sitemap)
