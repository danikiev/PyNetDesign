# -*- coding: utf-8 -*-
"""Sphinx configuration for the PyNetDesign documentation."""
import datetime
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

from sphinx_gallery.sorting import ExampleTitleSortKey

DOCS_SOURCE = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_SOURCE.parents[1]

# Sphinx must be able to import the package for autodoc and for the version number,
# and the local extensions under _ext
sys.path.insert(0, str(DOCS_SOURCE))
sys.path.insert(0, os.path.abspath("../.."))

# Render CHANGELOG.md into changelog.rst, so the changelog has a single source.
# The generated page is gitignored; edit CHANGELOG.md instead.
from _ext.changelog import generate_changelog_page  # noqa: E402

generate_changelog_page(PROJECT_ROOT, DOCS_SOURCE)

# -- Project information -----------------------------------------------------

project = "PyNetDesign"
project_summary = "A Python framework for microseismic monitoring network design"
author = "Denis Anikiev"
year = datetime.date.today().year
copyright = f"{year}, {author}"

try:
    release = pkg_version("pynetdesign")
except PackageNotFoundError:
    release = "dev"

version = release.split("+")[0]
if version == "unknown":
    version = "dev"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "sphinxcontrib.bibtex",
    "matplotlib.sphinxext.plot_directive",
    "numpydoc",
    "sphinx_gallery.gen_gallery",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "**.ipynb_checkpoints", "**.ipynb", "**.md5"]
source_suffix = {".rst": "restructuredtext"}
source_encoding = "utf-8-sig"
root_doc = "index"
pygments_style = "default"
add_function_parentheses = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# -- autodoc / autosummary / numpydoc ----------------------------------------

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_default_options = {"members": True}
autodoc_typehints = "none"

numpydoc_show_class_members = False
numpydoc_show_inherited_class_members = False
numpydoc_class_members_toctree = False

# -- Bibliography ------------------------------------------------------------

bibtex_bibfiles = ["references.bib"]
bibtex_reference_style = "author_year"

suppress_warnings = [
    "bibtex.duplicate_label",
    "bibtex.duplicate_citation",
    # sphinx_gallery_conf holds a sort-key class and therefore cannot be pickled into
    # the config cache; harmless, and unrelated to the documentation content
    "config.cache",
    # Fontawesome glyphs are an HTML embellishment: every icon in these sources sits
    # beside the link text that carries the meaning, so the PDF loses nothing by
    # dropping them. Rendering them instead would need fontawesome5.sty, which lives in
    # texlive-fonts-extra and is far too heavy to install for a few decorative glyphs
    "design.fa-build",
]

# -- Example gallery ---------------------------------------------------------

sphinx_gallery_conf = {
    # Where the example scripts live
    "examples_dirs": ["../../examples"],
    # Where the rendered gallery is written
    "gallery_dirs": ["examples"],
    # Run every example
    "filename_pattern": r"\.py",
    "download_all_examples": False,
    "within_subsection_order": ExampleTitleSortKey,
    "backreferences_dir": "api/generated/backreferences",
    "doc_module": "pynetdesign",
    "reference_url": {"pynetdesign": None},
}

# Always show the source that produced a figure
plot_include_source = True
plot_formats = ["png"]

# -- HTML output -------------------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_title = project
html_short_title = project
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
html_last_updated_fmt = "%b %d, %Y"
html_show_sourcelink = False

# Branding, from the PyNetDesign brand package. The transparent logo is used on both
# the light and the dark theme, so the mark keeps its own clear space and is never
# filtered or recoloured by the theme.
html_logo = "_static/pynetdesign-logo.svg"
html_favicon = "_static/favicon.ico"

# The documentation is also published as a single PDF. On GitHub Pages the site lives
# under a project subpath, so the link has to include the repository name there.
on_github_ci = os.environ.get("GITHUB_ACTIONS") == "true"
github_repository = os.environ.get("GITHUB_REPOSITORY", "")
github_repo_name = github_repository.split("/")[-1] if github_repository else ""

if on_github_ci and github_repo_name:
    pdf_url = f"/{github_repo_name}/_static/pynetdesign.pdf"
else:
    pdf_url = "/_static/pynetdesign.pdf"

html_theme_options = {
    "logo": {
        "image_light": "pynetdesign-logo.svg",
        "image_dark": "pynetdesign-logo.svg",
        "alt_text": "PyNetDesign",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/danikiev/PyNetDesign",
            "icon": "fab fa-github",
            "type": "fontawesome",
        },
        {
            "name": "Download as PDF",
            "url": pdf_url,
            "icon": "fas fa-file-pdf",
            "type": "fontawesome",
        },
    ],
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
    "show_nav_level": 2,
    "navigation_depth": 3,
    "collapse_navigation": True,
}

# Standalone pages read top to bottom, so they do not need a secondary sidebar
html_sidebars = {
    "getting_started": [],
    "methodology": [],
    "contributing": [],
    "changelog": [],
    "citing": [],
    "credits": [],
}

rst_epilog = f"""
.. |year| replace:: {year}
"""

# -- LaTeX / PDF output ------------------------------------------------------

# A single PDF of the whole documentation, published alongside the HTML as
# _static/pynetdesign.pdf and linked from the navigation bar and the landing page.
latex_documents = [
    (root_doc, "pynetdesign.tex", project, author, "manual"),
]

# LaTeX cannot include SVG, so the raster logo is used for the title page
latex_logo = "_static/pynetdesign-logo.png"

latex_elements = {
    "releasename": "version",
    "preamble": r"""
\usepackage{csquotes}
\usepackage[titles]{tocloft}
\usepackage{qrcode}
\AtEndDocument{%
\clearpage
\thispagestyle{empty}
\begin{center}
{\Large Online documentation}\par
\vspace{0.8cm}
\qrcode[height=5cm]{https://danikiev.github.io/PyNetDesign/}\par
\vspace{0.6cm}
\href{https://danikiev.github.io/PyNetDesign/}{danikiev.github.io/PyNetDesign}
\end{center}
}
    """,
    "maketitle": rf"""
\begin{{titlepage}}
\centering
\vspace*{{2.2cm}}
\begin{{center}}
\sphinxincludegraphics[width=0.8\textwidth]{{pynetdesign-logo.png}}\par
\end{{center}}
\vspace{{1.2cm}}
{{\Large {project_summary} \par}}
\vfill
{{\Large {author} \par}}
\vspace{{0.3cm}}
{{\large Version {release} \par}}
\vspace{{0.8cm}}
{{\large \today \par}}
\end{{titlepage}}
\clearpage
""",
}

# lualatex handles the unicode used in the methodology and the bibliography
latex_engine = "lualatex"
latex_use_xindy = False
