# SPDX-License-Identifier: BSD-2-Clause

# XXX(aki): This module is only really for the toolchain tests, the normal unit tests don't care
try:
	from torii.build.plat         import Platform

	from torii_boards.test.blinky import Blinky

	def _test_platform(platform: Platform):
		def test_platform(self):
			plat_name = type(platform).__name__
			platform.build(Blinky(), plat_name, do_build = True, do_program = False)

		return test_platform

except ImportError:
	pass
