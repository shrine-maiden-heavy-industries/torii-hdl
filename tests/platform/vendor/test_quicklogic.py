# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.quicklogic import QuicklogicPlatform

from .                                import ToriiToolchainTestCase

class QuicklogicToolchainTests(ToriiToolchainTestCase[QuicklogicPlatform]):
	TOOLCHAINS = ('QLSymbiflow', )

	class QuicklogicTestPlatform(QuicklogicPlatform):
		device  = ''
		package = ''

		def __init__(self, *, toolchain, device, package) -> None:
			self.device  = device
			self.package = package

			super().__init__(toolchain = toolchain)

		resources = []
		connectors = []

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
