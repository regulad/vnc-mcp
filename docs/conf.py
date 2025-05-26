"""Sphinx configuration."""

project = "vnc-mcp"
author = "Parker Wahle"
copyright = "2025, Parker Wahle"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
