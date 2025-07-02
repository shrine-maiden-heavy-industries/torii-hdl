# SPDX-License-Identifier: BSD-2-Clause

from torii.platform.vendor.altera import AlteraPlatform

from .                            import ToriiToolchainTestCase

def mistral_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Mistral')(func)

def quartus_toolchain_test(func):
	return ToriiToolchainTestCase.toolchain_test('Quartus')(func)

class AlteraToolchainTests(ToriiToolchainTestCase[AlteraPlatform]):
	TOOLCHAINS = ('Mistral', 'Quartus')

	@ToriiToolchainTestCase.toolchain_test()
	def test_dummy(self) -> None:
		self.assertTrue(True)
