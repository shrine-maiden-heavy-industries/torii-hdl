# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import warnings
from copy                    import deepcopy
from io                      import StringIO

from torii.diagnostics.hooks import (
	_WARN_HANDLER_RESTORE, DEFAULT_FANCY_CONTEXT, DEFAULT_FANCY_WIDTH, DEFAULT_STRIP_PATH, DEFAULT_USE_FANCY,
	WarningRenderingOptions, _get_console, _populate_options, _warning_handler, install_warning_handler,
	remove_warning_handler,
)

from ..utils                 import ToriiTestSuiteCase

class ToriiWarningHandlerTestCase(ToriiTestSuiteCase):

	def flush_torii_envs(self) -> None:
		os.environ.pop('TORII_WARNINGS_NOHANDLE', None)
		os.environ.pop('TORII_WARNINGS_NOFANCY', None)
		os.environ.pop('TORII_WARNINGS_CONTEXT', None)
		os.environ.pop('TORII_WARNINGS_WIDTH', None)
		os.environ.pop('TORII_WARNINGS_STRIP', None)

	def setUp(self) -> None:
		# Save state before we muck with it
		self.old_env = deepcopy(os.environ)
		self.old_handler = deepcopy(warnings.showwarning)
		self.old_filters = deepcopy(warnings.filters)

		# Ensure we always start with a clean env
		self.flush_torii_envs()

	def tearDown(self) -> None:
		# Restore state if we did muck with it
		os.environ = deepcopy(self.old_env)
		warnings.showwarning = deepcopy(self.old_handler)
		warnings.filters = deepcopy(self.old_filters)

		self.flush_torii_envs()

	def test_populate_options_defaults(self) -> None:

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

	def test_populate_options_set(self) -> None:

		os.environ['TORII_WARNINGS_NOFANCY'] = '1'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = False,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_CONTEXT'] = '10'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = 10,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_WIDTH'] = '1234'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = 1234,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_STRIP'] = '1'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = True
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_CONTEXT'] = '50'
		os.environ['TORII_WARNINGS_WIDTH'] = '10'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = 50,
			fancy_width = 10,
			strip_path = DEFAULT_STRIP_PATH
		))

	def test_populate_options_bogus(self) -> None:

		os.environ['TORII_WARNINGS_CONTEXT'] = 'meow'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_WIDTH'] = 'uwu'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_CONTEXT'] = '-10'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_WIDTH'] = '-50'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_CONTEXT'] = '3.14159'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_WIDTH'] = '1.3e7'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_CONTEXT'] = '0'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

		self.flush_torii_envs()

		os.environ['TORII_WARNINGS_WIDTH'] = '0'

		self.assertEqual(_populate_options(), WarningRenderingOptions(
			use_fancy = DEFAULT_USE_FANCY,
			fancy_context = DEFAULT_FANCY_CONTEXT,
			fancy_width = DEFAULT_FANCY_WIDTH,
			strip_path = DEFAULT_STRIP_PATH
		))

	def test_get_console(self) -> None:

		cons = _get_console(None)
		self.assertEqual(cons.file, sys.stdout)

		cons = _get_console(sys.stdout)
		self.assertEqual(cons.file, sys.stdout)

		buff = StringIO()
		cons = _get_console(buff)
		self.assertEqual(cons.file, buff)

	def test_handler_install(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)

		install_warning_handler()

		self.assertEqual(warnings.showwarning, _warning_handler)

	def test_handler_install_skip(self) -> None:

		os.environ['TORII_WARNINGS_NOHANDLE'] = '1'

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

		install_warning_handler()

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

	def test_handler_installed_already(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

		install_warning_handler()

		self.assertEqual(self.old_handler, _WARN_HANDLER_RESTORE)
		self.assertEqual(warnings.showwarning, _warning_handler)

		install_warning_handler()

		self.assertEqual(self.old_handler, _WARN_HANDLER_RESTORE)
		self.assertEqual(warnings.showwarning, _warning_handler)

	# TODO(aki): This test should be more more detailed/comprehensive
	def test_handler_install_warnings_filter(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)

		old_filters = deepcopy(warnings.filters)

		install_warning_handler()

		self.assertNotEqual(warnings.filters, old_filters)

	# TODO(aki): This test should be more more detailed/comprehensive
	def test_handler_install_warnings_filter_all(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)

		old_filters = deepcopy(warnings.filters)

		install_warning_handler(catch_all = True)

		self.assertNotEqual(warnings.filters, old_filters)

	def test_handler_remove_not_installed(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

		remove_warning_handler()

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

	def test_handler_remove_not_enabled(self) -> None:

		os.environ['TORII_WARNINGS_NOHANDLE'] = '1'

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

		remove_warning_handler()

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

	def test_handler_install_remove(self) -> None:

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)

		install_warning_handler()

		self.assertEqual(self.old_handler, _WARN_HANDLER_RESTORE)
		self.assertEqual(warnings.showwarning, _warning_handler)

		remove_warning_handler()

		self.assertEqual(self.old_handler, warnings.showwarning)
		self.assertEqual(warnings.showwarning, _WARN_HANDLER_RESTORE)
