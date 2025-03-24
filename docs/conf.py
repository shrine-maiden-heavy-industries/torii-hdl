# SPDX-License-Identifier: BSD-2-Clause
import os, sys, datetime
from pathlib import Path
sys.path.insert(0, os.path.abspath('.'))

from torii import __version__ as torii_version

ROOT_DIR = (Path(__file__).parent).parent

project   = 'Torii-HDL'
version   = torii_version
release   = version.split('+')[0]
copyright = f'{datetime.date.today().year}, Shrine Maiden Heavy Industries'
language  = 'en'

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.doctest',
	'sphinx.ext.extlinks',
	'sphinx.ext.githubpages',
	'sphinx.ext.intersphinx',
	'sphinx.ext.napoleon',
	'sphinx.ext.todo',
	'sphinx_inline_tabs',
	'sphinxcontrib.wavedrom',
	'myst_parser',
	'sphinx_rtd_theme',
]

source_suffix = {
	'.rst': 'restructuredtext',
	'.md': 'markdown',
}

extlinks = {
	'issue': ('https://github.com/shrine-maiden-heavy-industries/torii-hdl/issues/%s', 'torii/%s'),
	'pypi':  ('https://pypi.org/project/%s/', '%s'),
}

pygments_style         = 'monokai'
autodoc_member_order   = 'bysource'
graphviz_output_format = 'svg'
todo_include_todos     = True

intersphinx_mapping = {
	'python': ('https://docs.python.org/3', None)
}

napoleon_google_docstring              = False
napoleon_numpy_docstring               = True
napoleon_use_ivar                      = True
napoleon_use_admonition_for_notes      = True
napoleon_use_admonition_for_examples   = True
napoleon_use_admonition_for_references = True
napoleon_custom_sections  = [
	('Attributes', 'params_style'),
	'Platform overrides'
]

myst_heading_anchors = 3

templates_path = [
	'_templates',
]

html_context = {
	'display_lower_left': False,
	'current_language'  : language,
	'current_version'   : version,
	'version'           : version,
	'display_github'    : True,
	'github_user'       : 'shrine-maiden-heavy-industries',
	'github_repo'       : 'torii-hdl',
	'github_version'    : 'main/docs/',
	'versions'          : [
		('latest', '/latest')
	]
}

html_baseurl     = 'https://torii.shmdn.link/'
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
	'js/wavedrom.min.js',
	'js/wavedrom.skin.js',
]

html_style = 'css/styles.css'

offline_skin_js_path     = '_static/js/wavedrom.skin.js'
offline_wavedrom_js_path = '_static/js/wavedrom.min.js'

linkcheck_ignore = [
	'https://www.intel.com/content/www/us/en/products/details/fpga/development-tools/quartus-prime.html',
	'https://www.xilinx.com/products/design-tools/ise-design-suite.html',
	'https://www.xilinx.com/products/design-tools/vivado.html',
	# Sphinx linkc-check and GitLab readme anchors don't get along
	'https://gitlab.com/surfer-project/surfer#installation',
]
