# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.lattice.ice40 import ICE40Platform

from ..                                  import ToriiToolchainTestCase

def icestorm_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('IceStorm')(func)

def lse_icecube2_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('LSE-iCECube2')(func)

def synp_icecube2_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Synplify-iCECube2')(func)

class iCE40ToolchainTests(ToriiToolchainTestCase[ICE40Platform]):
	TOOLCHAINS = ('IceStorm', 'LSE-iCECube2', 'Synplify-iCECube2')

	class ICE40TestPlatform(ICE40Platform):
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
