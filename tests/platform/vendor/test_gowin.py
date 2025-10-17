# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.gowin import GowinPlatform

from .                           import ToriiToolchainTestCase

def apicula_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Apicula')(func)

def gowin_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Gowin')(func)

class GowinToolchainTests(ToriiToolchainTestCase[GowinPlatform]):
	TOOLCHAINS = ('Apicula', 'Gowin')

	class GowinTestPlatform(GowinPlatform):
		part   = ''
		family = ''

		def __init__(self, *, toolchain, part, family) -> None:
			self.part   = part
			self.family = family

			super().__init__(toolchain = toolchain)

		resources = []
		connectors = []

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
