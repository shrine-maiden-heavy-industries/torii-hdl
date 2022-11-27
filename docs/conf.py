# SPDX-License-Identifier: BSD-2-Clause
import os, sys
sys.path.insert(0, os.path.abspath('.'))

import torii

project = 'Torii-HDL'
version = torii.__version__
release = version.split('+')[0]
copyright = '2022, Shrine Maiden Heavy Industries'
language  = 'en'

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.doctest',
	'sphinx.ext.githubpages',
	'sphinx.ext.intersphinx',
	'sphinx.ext.napoleon',
	'sphinx.ext.todo',
	'sphinxcontrib.platformpicker',
	'sphinxcontrib.wavedrom',
	'myst_parser',
	'sphinx_rtd_theme',
]

with open(".gitignore") as f:
	exclude_patterns = [line.strip() for line in f.readlines()]

source_suffix = {
	'.rst': 'restructuredtext',
	'.md': 'markdown',
}

root_doc = 'cover'

pygments_style         = 'monokai'
autodoc_member_order   = 'bysource'
graphviz_output_format = 'svg'
todo_include_todos     = True

intersphinx_mapping = {
	'python': ('https://docs.python.org/3', None)
}


napoleon_google_docstring = False
napoleon_numpy_docstring  = True
napoleon_use_ivar         = True
napoleon_custom_sections  = [
	'Platform overrides'
]

html_baseurl     = 'https://shrine-maiden-heavy-industries.github.io/torii-hdl/'
html_theme       = 'sphinx_rtd_theme'
html_copy_source = False

html_theme_options = {
	'collapse_navigation' : False,
	'style_external_links': True,
}

html_static_path = [
	'_static'
]

html_css_files = [
	'css/styles.css'
]

html_js_files = [
	'js/mermaid.min.js',
	'js/wavedrom.min.js',
	'js/wavedrom.skin.js',
]

html_style = 'css/styles.css'

offline_skin_js_path = '_static/js/wavedrom.skin.js'
offline_wavedrom_js_path = '_static/js/wavedrom.min.js'
