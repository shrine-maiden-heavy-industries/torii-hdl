# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.xilinx import XilinxPlatform

from .                            import ToriiToolchainTestCase

def vivado_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Vivado')(func)

def ise_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('ISE')(func)

class XilinxVivadoToolchainTests(ToriiToolchainTestCase[XilinxPlatform]):
	TOOLCHAINS = ('Vivado', 'ISE')

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
