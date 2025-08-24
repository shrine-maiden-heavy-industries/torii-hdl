# SPDX-License-Identifier: BSD-2-Clause
# torii: UnusedElaboratable=no

from contextlib    import contextmanager

from torii.hdl.ast import Signal, Value
from torii.hdl.dsl import Module, Statement
from torii.hdl.ir  import Fragment
from torii.sim     import Settle, Simulator
from torii.util    import flatten

from ..utils       import ToriiTestSuiteCase
from .sim_harness  import SimulatorIntegrationTestsMixin, SimulatorRegressionTestMixin, SimulatorUnitTestsMixin

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

class PysimRegressionTestCase(ToriiTestSuiteCase, SimulatorRegressionTestMixin):
	def get_simulator(self, dut) -> Simulator:
		return Simulator(dut, engine = 'pysim')

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
