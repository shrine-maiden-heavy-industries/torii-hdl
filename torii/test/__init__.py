# SPDX-License-Identifier: BSD-2-Clause

from functools import wraps
from math      import ceil
from os        import getenv
from pathlib   import Path
from typing    import Optional
from unittest  import TestCase

from ..hdl.ast import Signal
from ..hdl.ir  import Fragment
from ..sim     import Settle, Simulator
from .mock     import MockPlatform

__all__ = (
	'ToriiTestCase',
	'sim_test',
)

class ToriiTestCase(TestCase):
	'''Torii test case wrapper for pythons unittest library

	This class wraps the :py:class:`TestCase` class from the `unittest` module
	from the python standard lib. It has useful methods for testing and simulating
	Torii based gateware.

	Attributes
	----------
	domains : Tuple[Tuple[str, float]]
		The collection of clock domains and frequencies
	out_dir : str
		The test output directory.
	dut : Elaboratable
		The elaboratable to test.
	dut_args : dict[str, Any]
		The initialization arguments for the elaboratable.
	platform : MockPlatform, Any
		The platform passed to the Elaboratable DUT

	'''

	domains   = (('sync', 1e8),)
	out_dir   = None
	dut       = None
	dut_args  = {}
	platform  = MockPlatform()

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self._frag = None

	@property
	def vcd_name(self) -> str:
		''' Return the name used to generate VCD files '''
		return f'test-{self.__class__.__name__}'

	def clk_period(self, domain : Optional[str] = None) -> float:
		''' Returns the period of the clock on the given domain '''
		if domain is None:
			return 1 / self.domains[0][1]

		freq = next(d[1] for d in self.domains if d[0] == domain)

		return 1 / freq

	def run_sim(self, *, suffix : Optional[str] = None) -> None:
		'''Run the simulation

		If the environment variable ``TORII_TEST_INHIBIT_VCD``
		is set, then no VCDs will be generated.

		Keyword Args
		------------
		suffix : str
			The option VCD test case suffix.
		'''

		if getenv('TORII_TEST_INHIBIT_VCD', default = False):
			self.sim.reset()
			self.sim.run()
		else:
			out_name = f'{self.vcd_name}{f"-{suffix}" if suffix is not None else ""}.vcd'
			out_file = self.out_dir / out_name

			with self.sim.write_vcd(out_file):
				self.sim.reset()
				self.sim.run()

	def setUp(self) -> None:

		self.dut   = self.init_dut()
		self._frag = Fragment.get(self.dut, self.platform)
		self.sim   = Simulator(self._frag)

		if self.out_dir is None:
			if (Path.cwd() / 'build').exists():
				self.out_dir = Path.cwd() / 'build' / 'tests'
			else:
				self.out_dir = Path.cwd() / 'test-vcds'

		self.out_dir.mkdir(exist_ok = True, parents = True)

		for d, _ in self.domains:
			self.sim.add_clock(self.clk_period(d), domain = d)

	def init_dut(self):
		''' Initialize and return the DUT '''
		return self.dut(**self.dut_args)

	def init_signals(self):

		yield Signal()

	def wait_for(self, time : float, domain : Optional[str] = None):
		''' Waits for the number time units.

		Parameters
		----------
		time : float
			The unit of time to wait.

		'''

		c = ceil(time / self.clk_period(domain))

		yield from self.step(c)

	@staticmethod
	def pulse(sig: Signal , *, neg: bool = False, post_step: bool = True):
		'''Pulse a given signal.

		Pulse a given signal to 1 then 0, or if `neg` is set to `True` pulse
		from 1 to 0.

		Parameters
		----------
		sig : Signal
			The signal to pulse.

		Keyword Args
		------------
		neg : bool
			Inverts the pulse direction.
		post_step : bool
			Insert additional simulation step after pulse.

		'''
		if not neg:
			yield sig.eq(1)
			yield
			yield sig.eq(0)
		else:
			yield sig.eq(0)
			yield
			yield sig.eq(1)
		if post_step:
			yield


	@staticmethod
	def pulse_pos(sig : Signal, *, post_step : bool = True):
		'''Inserts a positive pulse on the given signal

		Parameters
		----------
		sig : Signal
			The signal to pulse.

		Keyword Args
		------------
		post_step : bool
			Insert additional simulation step after pulse.

		'''

		yield from ToriiTestCase.pulse(sig, neg = False, post_step = post_step)

	@staticmethod
	def pulse_neg(sig : Signal, *, post_step : bool = True):
		'''Inserts a negative pulse on the given signal

		Parameters
		----------
		sig : Signal
			The signal to pulse.

		Keyword Args
		------------
		post_step : bool
			Insert additional simulation step after pulse.

		'''

		yield from ToriiTestCase.pulse(sig, neg = True, post_step = post_step)

	@staticmethod
	def step(cycles : int):
		'''Step simulator.

		This advances the simulation by the given number of cycles.

		Parameters
		----------
		cycles : int
			Number of cycles to step the simulator.

		'''

		for _ in range(cycles + 1):
			yield

	@staticmethod
	def settle(count : int = 1):
		'''Settle simulator.

		This advances the simulation by the given number of settles.

		Parameters
		----------
		count : int
			Number of settles to invoke in the simulator.

		'''
		for _ in range(count):
			yield Settle()
			yield

	@staticmethod
	def wait_until_high(strobe : Signal, *, timeout : int = None):
		'''Run simulation until signal goes high.

		Runs the simulation while checking for the positive edge of the `strobe`
		signal.

		Will run until a positive edge is seen, or if `timeout` is set, will run
		for at most that many cycles.

		This is the positive counterpart for the :py:func:`wait_until_low` method.

		Parameters
		----------
		strobe : Signal
			The signal to check the strobe for.

		Keyword Args
		------------
		timeout : int
			The max number of cycles to wait.
		'''

		elapsed_cycles = 0
		while not (yield strobe):
			yield
			elapsed_cycles += 1
			if timeout and elapsed_cycles > timeout:
				raise RuntimeError(f'Timeout waiting for \'{strobe.name}\' to go high')

	@staticmethod
	def wait_until_low(strobe : Signal, *, timeout : int = None):
		'''Run simulation until signal goes low.

		Runs the simulation while checking for the negative edge of the `strobe`
		signal.

		Will run until a negative edge is seen, or if `timeout` is set, will run
		for at most that many cycles.

		This is the negative counterpart for the :py:func:`wait_until_high` method.

		Parameters
		----------
		strobe : Signal
			The signal to check the strobe for.

		Keyword Args
		------------
		timeout : int
			The max number of cycles to wait.
		'''

		elapsed_cycles = 0
		while (yield strobe):
			yield
			elapsed_cycles += 1
			if timeout and elapsed_cycles > timeout:
				raise RuntimeError(f'Timeout waiting for \'{strobe.name}\' to go low')

def sim_test(*, domain : str = None, defer : bool = False):
	'''Simulation test case decorator

	Parameters
	----------
	func
		The decorated function.

	Keyword Args
	------------
	domain : str
		The clock domain this case belongs to.

	'''
	def _test(func):
		def _run(self):
			@wraps(func)
			def sim_case():
				yield from self.init_signals()
				yield from func(self)

			if domain is None:
				test_domain = self.domains[0][0]
			else:
				test_domain = domain

			self.sim.add_sync_process(sim_case, domain = test_domain)
			if not defer:
				self.run_sim(suffix = func.__name__)
		return _run
	return _test
