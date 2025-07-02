# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.quicklogic import QuicklogicPlatform

from .                                import ToriiToolchainTestCase

class QuicklogicToolchainTests(ToriiToolchainTestCase[QuicklogicPlatform]):
	TOOLCHAINS = ('QLSymbiflow', )

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
