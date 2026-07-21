project = "PyWorldAtlas"
author = "PyWorldAtlas maintainers"
copyright = "2026, PyWorldAtlas maintainers"
release = "0.3.0"
version = "0.2"
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
html_title = "PyWorldAtlas 0.3.0"
html_short_title = "PyWorldAtlas"
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
}
exclude_patterns = ["_build"]
