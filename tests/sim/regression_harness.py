# SPDX-License-Identifier: BSD-2-Clause

import os

from torii.hdl.ast   import Cat, Const, Signal
from torii.hdl.cd    import ClockDomain
from torii.hdl.dsl   import Module

from ._harness_types import SimulatorRegressionTestMixinBase

class SimulatorRegressionTestMixin(SimulatorRegressionTestMixinBase):
	def test_bug_325(self):
		dut = Module()
		dut.d.comb += Signal().eq(Cat())
		self.get_simulator(dut).run()

	def test_bug_473(self):
		sim = self.get_simulator(Module())

		def process():
			self.assertEqual((yield -(Const(0b11, 2).as_signed())), 1)
		sim.add_process(process)
		sim.run()

	def test_bug_595(self):
		dut = Module()
		with dut.FSM(name = 'name with space'):
			with dut.State(0):
				pass
		sim = self.get_simulator(dut)
		with self.assertRaisesRegex(
			NameError,
			r'^Signal \'bench\.top\.name with space_state\' contains a whitespace character$'
		):
			with open(os.path.devnull, 'w') as f:
				with sim.write_vcd(f):
					sim.run() # :nocov:

	def test_bug_588(self):
		dut = Module()
		a = Signal(32)
		b = Signal(32)
		z = Signal(32)
		dut.d.comb += z.eq(a << b)
		with self.assertRaisesRegex(
			OverflowError,
			r'^Value defined at .+?[\\/]regression_harness\.py:\d+ is 4294967327 bits wide, '
			r'which is unlikely to simulate in reasonable time$'
		):
			self.get_simulator(dut)

	def test_bug_566(self):
		dut = Module()
		dut.d.sync += Signal().eq(0)
		sim = self.get_simulator(dut)
		with self.assertWarnsRegex(
			UserWarning,
			r'^Adding a clock process that drives a clock domain object named \'sync\', '
			r'which is distinct from an identically named domain in the simulated design$'
		):
			sim.add_clock(1e-6, domain = ClockDomain('sync'))

	def test_bug_826(self):
		sim = self.get_simulator(Module())

		def process():
			self.assertEqual((yield Const(0b0000, 4) | ~Const(1, 1)), 0b0000)
			self.assertEqual((yield Const(0b1111, 4) & ~Const(1, 1)), 0b0000)
			self.assertEqual((yield Const(0b1111, 4) ^ ~Const(1, 1)), 0b1111)

		sim.add_process(process)
		sim.run()
