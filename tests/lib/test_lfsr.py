# SPDX-License-Identifier: BSD-2-Clause

from torii.hdl         import Const, Elaboratable, Module
from torii.lib.lfsr    import LFSR, LFSRDir, LFSRKind
from torii.test        import ToriiTestCase
from torii.util.tracer import get_var_name

from ..utils           import ToriiTestSuiteCase

class LFSR_DUT(Elaboratable):
	def __init__(self, loopback: bool = False, input_const: Const | None = None, **lfsr_args) -> None:
		self.lfsr_args = lfsr_args
		self.loopback  = loopback
		self.in_const  = input_const

	def elaborate(self, platform) -> Module:
		m = Module()

		m.submodules.lfsr = lfsr = LFSR(**self.lfsr_args)

		self.output = lfsr.output
		self.input  = lfsr.input
		self.state  = lfsr.state
		self.en     = lfsr.en

		if self.loopback:
			m.d.comb += [
				lfsr.input.eq(lfsr.output)
			]
		elif self.in_const is not None:
			m.d.comb += [
				lfsr.input.eq(self.in_const)
			]

		return m


def make_lfsr_test(
	*, polynomial: int, state_width: int, io_width: int, seed: int, kind: LFSRKind, direction: LFSRDir,
	feed_forward: bool, loopback: bool = False, input_const: Const | None = None, refgen = None
) -> type[ToriiTestSuiteCase]:
	class _LFSRTestCase(ToriiTestSuiteCase):
		dut: LFSR_DUT | type[LFSR_DUT] = LFSR_DUT
		dut_args = {
			'loopback': loopback,
			'input_const': input_const,
			'polynomial': polynomial,
			'state_width': state_width,
			'io_width': io_width,
			'seed': seed,
			'kind': kind,
			'direction': direction,
			'feed_forward': feed_forward,
		}

		@ToriiTestCase.simulation
		@ToriiTestCase.sync_domain(domain = 'sync')
		def lfsr_test(self):

			cycle_count = (2 ** self.dut.state.width) - 1
			self.assertEqual((yield self.dut.state), self.dut_args['seed'])

			while cycle_count > 1:
				yield
				cycle_count -= 1

			self.assertEqual((yield self.dut.state), self.dut_args['seed'])

	# XXX(aki): Ignore this unholy mess
	test_name_stub = get_var_name()
	_LFSRTestCase.__name__ = f'{test_name_stub}TestCase'
	setattr(_LFSRTestCase, f'test_lfsr_{test_name_stub}', _LFSRTestCase.lfsr_test)

	return _LFSRTestCase


PRBS7 = make_lfsr_test(
	polynomial   = (1 << 7) | (1 << 6) | (1 << 0), # x^7 + x^6 + x^0
	state_width  = 7,
	io_width     = 1,
	seed         = 0x2,
	kind         = LFSRKind.Galois,
	direction    = LFSRDir.MSb,
	feed_forward = False
)

Generic = make_lfsr_test(
	polynomial   = (1 << 16) | (1 << 14) | (1 << 13) | ( 1 << 11) | (1 << 0), # x^16 + x^14 + x^13 + x^11 + x^0
	state_width  = 16,
	io_width     = 1,
	seed         = 0x8735,
	kind         = LFSRKind.Fibonacci,
	direction    = LFSRDir.LSb,
	feed_forward = False
)
