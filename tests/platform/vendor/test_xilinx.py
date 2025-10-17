# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.xilinx import XilinxPlatform

from .                            import ToriiToolchainTestCase

def vivado_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Vivado')(func)

def ise_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('ISE')(func)

class XilinxVivadoToolchainTests(ToriiToolchainTestCase[XilinxPlatform]):
	TOOLCHAINS = ('Vivado', 'ISE')

	class XilinxTestPlatform(XilinxPlatform):
		device  = ''
		package = ''
		speed   = ''

		def __init__(self, *, toolchain, device, package, speed) -> None:
			self.device  = device
			self.package = package
			self.speed   = speed

			super().__init__(toolchain = toolchain)

		resources = []
		connectors = []

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
