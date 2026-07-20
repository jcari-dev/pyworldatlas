project = "PyWorldAtlas"
author = "PyWorldAtlas maintainers"
release = "0.1.0"
version = "0.1"
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
html_title = "PyWorldAtlas 0.1.0"
exclude_patterns = ["_build"]
