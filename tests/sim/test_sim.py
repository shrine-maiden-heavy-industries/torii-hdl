# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

import os
from contextlib    import contextmanager

from torii.hdl.ast import Cat, Const, Signal, Value
from torii.hdl.cd  import ClockDomain
from torii.hdl.dsl import Module, Statement
from torii.hdl.ir  import Fragment
from torii.sim     import Settle, Simulator
from torii.util    import flatten

from ..utils       import ToriiTestSuiteCase
from .sim_harness  import SimulatorUnitTestsMixin, SimulatorIntegrationTestsMixin

class PysimSimulatorUnitTestCase(ToriiTestSuiteCase, SimulatorUnitTestsMixin):
	def assertStatement(self, stmt, inputs, output, reset = 0):
		inputs = [Value.cast(i) for i in inputs]
		output = Value.cast(output)

		isigs = [ Signal(i.shape(), name = n) for i, n in zip(inputs, 'abcd') ]
		osig  = Signal(output.shape(), name = 'y', reset = reset)

		stmt = stmt(osig, *isigs)
		frag = Fragment()
		frag.add_statements(stmt)
		for signal in flatten(s._lhs_signals() for s in Statement.cast(stmt)):
			frag.add_driver(signal)

		sim = Simulator(frag, engine = 'pysim')

		def process():
			for isig, input in zip(isigs, inputs):
				yield isig.eq(input)
			yield Settle()
			self.assertEqual((yield osig), output.value)

		sim.add_process(process)
		with sim.write_vcd('test.vcd', 'test.gtkw', traces = [ *isigs, osig ]):
			sim.run()

class PysimSimulatorIntegrationTestCase(ToriiTestSuiteCase, SimulatorIntegrationTestsMixin):
	@contextmanager
	def assertSimulation(self, module, deadline = None):
		sim = Simulator(module, engine = 'pysim')
		yield sim
		with sim.write_vcd('test.vcd', 'test.gtkw'):
			if deadline is None:
				sim.run()
			else:
				sim.run_until(deadline)

class SimulatorRegressionTestCase(ToriiTestSuiteCase):
	def test_bug_325(self):
		dut = Module()
		dut.d.comb += Signal().eq(Cat())
		Simulator(dut).run()

	def test_bug_473(self):
		sim = Simulator(Module())

		def process():
			self.assertEqual((yield -(Const(0b11, 2).as_signed())), 1)
		sim.add_process(process)
		sim.run()

	def test_bug_595(self):
		dut = Module()
		with dut.FSM(name = 'name with space'):
			with dut.State(0):
				pass
		sim = Simulator(dut)
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
			r'^Value defined at .+?[\\/]test_sim\.py:\d+ is 4294967327 bits wide, '
			r'which is unlikely to simulate in reasonable time$'
		):
			Simulator(dut)

	def test_bug_566(self):
		dut = Module()
		dut.d.sync += Signal().eq(0)
		sim = Simulator(dut)
		with self.assertWarnsRegex(
			UserWarning,
			r'^Adding a clock process that drives a clock domain object named \'sync\', '
			r'which is distinct from an identically named domain in the simulated design$'
		):
			sim.add_clock(1e-6, domain = ClockDomain('sync'))

	def test_bug_826(self):
		sim = Simulator(Module())

		def process():
			self.assertEqual((yield Const(0b0000, 4) | ~Const(1, 1)), 0b0000)
			self.assertEqual((yield Const(0b1111, 4) & ~Const(1, 1)), 0b0000)
			self.assertEqual((yield Const(0b1111, 4) ^ ~Const(1, 1)), 0b1111)

		sim.add_process(process)
		sim.run()

# TODO(aki): Figure out a better name
class SimulatorEngineTestCase(ToriiTestSuiteCase):
	def test_external_sim_engine(self):
		from torii.sim._base import BaseEngine

		class DummyEngine(BaseEngine):
			def __init__(self, fragment) -> None:
				pass

		_ = Simulator(Module(), engine = DummyEngine)

	def test_invalid_simulator_engine(self):
		with self.assertRaisesRegex(
			TypeError,
			r'^The specified engine \'NotAValidEngineName\' is not a known simulation engine name, or simulation '
			'engine class$'
		):
			_ = Simulator(Module(), engine = 'NotAValidEngineName') # type: ignore

		with self.assertRaisesRegex(
			TypeError,
			r'^The specified engine <class \'object\'> is not a known simulation engine name, or simulation '
			'engine class$'
		):
			_ = Simulator(Module(), engine = object) # type: ignore
