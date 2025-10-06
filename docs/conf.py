"""Sphinx configuration for the RAG LLM technical documentation."""

from __future__ import annotations

import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_ROOT)

project = "RAG LLM Pipeline"
author = "Windsurf Engineering"
release = "0.2.0"
version = release
copyright = f"{datetime.now():%Y}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.githubpages",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
]

# Autodoc settings
autosummary_generate = True
autodoc_typehints = 'description'
add_module_names = False

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True

# Todo settings
todo_include_todos = True
todo_link_only = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
    'transformers': ('https://huggingface.co/docs/transformers/main/en/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/20/', None),
    'langchain': ('https://python.langchain.com/docs/', None),
}

# Mermaid configuration
mermaid_version = "10.9.1"
mermaid_output_format = "raw"
mermaid_init_js = "mermaid.initialize({startOnLoad:true, theme: 'default'});"

# Copy button configuration
copybutton_prompt_text = r'>>> |\.\.\. |\$ |In \[\d+\]: |\s*\.\.\.: |\s*\$ |\s*# |\s*>>> '
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = '\\'

# Sphinx design configuration
html_static_path = ['_static']
html_css_files = ['css/custom.css']
html_js_files = ['js/custom.js']

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'show_prev_next': True,
    'style_external_links': True,
    'github_url': 'https://github.com/aniketsharma21/rag_llm',
    'use_edit_page_button': True,
    'repository_url': 'https://github.com/aniketsharma21/rag_llm',
    'repository_branch': 'master',
    'path_to_docs': 'docs',
    'use_issues_button': True,
    'use_repository_button': True,
    'use_download_button': True,
}

intersphinx_mapping = {
    "python": (
        "https://docs.python.org/3",
        "https://docs.python.org/3/objects.inv",
    ),
    "pydantic": (
        "https://docs.pydantic.dev/latest/",
        "https://docs.pydantic.dev/latest/objects.inv",
    ),
}

templates_path = ["_templates"]
exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_title = "RAG LLM Technical Documentation"
html_theme_options = {
    "repository_url": "https://github.com/aniketsharma21/rag_llm",
    "use_repository_button": True,
    "path_to_docs": "docs",
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
}

copybutton_prompt_is_regexp = True
copybutton_prompt_text = r"^>>> |^\$ |^In \[[0-9]+\]: "
copybutton_only_copy_prompt_lines = False

pygments_style = "monokai"

mermaid_version = "10.9.1"
mermaid_output_format = "raw"

rst_prolog = """
.. |project| replace:: RAG LLM Pipeline
.. |api_module| replace:: ``src.api``
.. |rag_chain| replace:: ``src.llm.EnhancedRAGChain``
"""

def setup(app):
    app.add_css_file("custom.css")
