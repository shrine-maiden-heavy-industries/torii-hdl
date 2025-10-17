# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.lattice.machxo_2_3l import MachXO2Or3LPlatform

from ..                                        import ToriiToolchainTestCase

def trellis_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Trellis')(func)

def diamond_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('diamond')(func)

class MachXO2Or3LToolchainTests(ToriiToolchainTestCase[MachXO2Or3LPlatform]):
	TOOLCHAINS = ('Trellis', 'Diamond')

	class MachXO2Or3LTestPlatform(MachXO2Or3LPlatform):
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
