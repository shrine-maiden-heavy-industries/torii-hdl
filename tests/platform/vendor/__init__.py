# SPDX-License-Identifier: BSD-2-Clause

from functools        import wraps
from os               import getenv
from typing           import Generic, TypeVar
from unittest         import TestCase

from torii.build.plat import Platform
from torii.hdl        import Elaboratable, Module, Signal

TORII_TOOLCHAIN_TEST = getenv('TORII_TOOLCHAIN_TEST')

_T = TypeVar('_T', bound = Platform)

class ToriiToolchainTestCase(TestCase, Generic[_T]):

	TOOLCHAINS: tuple[str, ...]
	CURRENT_TOOLCHAIN: str
	PLATFORM: _T

	def __init__(self, method_name: str = 'runTest') -> None:
		super().__init__(method_name)

	@staticmethod
	def toolchain_test(toolchain: str | None = None):
		def _test(func):
			@wraps(func)
			def _register(self: ToriiToolchainTestCase):
				if (
					TORII_TOOLCHAIN_TEST is None or
					TORII_TOOLCHAIN_TEST not in self.TOOLCHAINS or
					(toolchain is not None and TORII_TOOLCHAIN_TEST != toolchain)
				):
					self.skipTest('Torii Toolchain Tests Disabled')
				else:
					self.CURRENT_TOOLCHAIN = TORII_TOOLCHAIN_TEST
					func(self)
			return _register
		return _test

class DUTCounter(Elaboratable):
	def __init__(self) -> None:
		self.en = Signal()
		self.ovf = Signal()
		self.count = Signal()

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		m.d.comb += [
			self.ovf.eq(self.count == 13)
		]

		with m.If(self.en):
			with m.If(self.ovf):
				m.d.sync += [
					self.count.eq(0),
				]
			with m.Else():
				m.d.sync += [
					self.count.inc()
				]

		return m
