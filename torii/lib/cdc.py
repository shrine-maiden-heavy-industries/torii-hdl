# SPDX-License-Identifier: BSD-2-Clause

from typing    import Literal

from ..hdl.ast import ClockSignal, ResetSignal, Signal
from ..hdl.cd  import ClockDomain
from ..hdl.dsl import Module
from ..hdl.ir  import Elaboratable

__all__ = (
	'AsyncFFSynchronizer',
	'FFSynchronizer',
	'PulseSynchronizer',
	'ResetSynchronizer',
)

def _check_stages(stages: int):
	if not isinstance(stages, int) or stages < 1:
		raise TypeError(f'Synchronization stage count must be a positive integer, not {stages!r}')
	if stages < 2:
		raise ValueError('Synchronization stage count may not safely be less than 2')

class FFSynchronizer(Elaboratable):
	'''
	Resynchronize a signal to a different clock domain.

	Consists of a chain of flip-flops. Eliminates metastabilities at the output, but provides
	no other guarantee as to the safe domain-crossing of a signal.

	Parameters
	----------
	i : Signal(n), in
		Signal to be resynchronized.
	o : Signal(n), out
		Signal connected to synchronizer output.
	o_domain : str
		Name of output clock domain.
	reset : int
		Reset value of the flip-flops. On FPGAs, even if ``reset_less`` is ``True``,
		the :class:`FFSynchronizer` is still set to this value during initialization.
	reset_less : bool
		If ``True`` (the default), this :class:`FFSynchronizer` is unaffected by ``o_domain``
		reset. See the note below for details.
	stages : int, >=2
		Number of synchronization stages between input and output. The lowest safe number is 2,
		with higher numbers reducing MTBF further, at the cost of increased latency.
	max_input_delay : None or float
		Maximum delay from the input signal's clock to the first synchronization stage, in seconds.
		If specified and the platform does not support it, elaboration will fail.

	.. note::

		:class:`FFSynchronizer` is non-resettable by default. Usually this is the safest option;
		on FPGAs the :class:`FFSynchronizer` will still be initialized to its ``reset`` value when
		the FPGA loads its configuration.

		However, in designs where the value of the :class:`FFSynchronizer` must be valid immediately
		after reset, consider setting ``reset_less`` to ``False`` if any of the following is true:

		- You are targeting an ASIC, or an FPGA that does not allow arbitrary initial flip-flop states;
		- Your design features warm (non-power-on) resets of ``o_domain``, so the one-time
		  initialization at power on is insufficient;
		- Your design features a sequenced reset, and the :class:`FFSynchronizer` must maintain
		  its reset value until ``o_domain`` reset specifically is de-asserted.

		:class:`FFSynchronizer` is reset by the ``o_domain`` reset only.

	Platform overrides
	------------------
	Define the ``get_ff_sync`` platform method to override the implementation of
	:class:`FFSynchronizer`, e.g. to instantiate library cells directly.

	''' # noqa: E101

	def __init__(
		self, i: Signal, o: Signal, *, o_domain: str = 'sync', reset: int = 0,
		reset_less: bool = True, stages: int = 2, max_input_delay: float | None = None
	) -> None:
		_check_stages(stages)

		self.i = i
		self.o = o

		self._reset      = reset
		self._reset_less = reset_less
		self._o_domain   = o_domain
		self._stages     = stages

		self._max_input_delay = max_input_delay

	def elaborate(self, platform) -> Module:
		if hasattr(platform, 'get_ff_sync'):
			return platform.get_ff_sync(self)

		if self._max_input_delay is not None:
			raise NotImplementedError(
				f'Platform \'{type(platform).__name__}\' does not support constraining input delay for FFSynchronizer'
			)

		m = Module()
		flops = [
			Signal(self.i.shape(), name = f'stage{index}', reset = self._reset, reset_less = self._reset_less)
			for index in range(self._stages)
		]
		for i, o in zip((self.i, *flops), flops):
			m.d[self._o_domain] += o.eq(i)
		m.d.comb += self.o.eq(flops[-1])
		return m

class AsyncFFSynchronizer(Elaboratable):
	'''
	Synchronize de-assertion of an asynchronous signal.

	The signal driven by the :class:`AsyncFFSynchronizer` is asserted asynchronously and de-asserted
	synchronously, eliminating metastability during de-assertion.

	This synchronizer is primarily useful for resets and reset-like signals.

	Parameters
	----------
	i : Signal(1), in
		Asynchronous input signal, to be synchronized.
	o : Signal(1), out
		Synchronously released output signal.
	o_domain : str
		Name of clock domain to synchronize to.
	stages : int, >=2
		Number of synchronization stages between input and output. The lowest safe number is 2,
		with higher numbers reducing MTBF further, at the cost of increased de-assertion latency.
	async_edge : str
		The edge of the input signal which causes the output to be set. Must be one of "pos" or "neg".
	max_input_delay : None or float
		Maximum delay from the input signal's clock to the first synchronization stage, in seconds.
		If specified and the platform does not support it, elaboration will fail.

	Platform overrides
	------------------
	Define the ``get_async_ff_sync`` platform method to override the implementation of
	:class:`AsyncFFSynchronizer`, e.g. to instantiate library cells directly.

	'''

	def __init__(
		self, i: Signal, o: Signal, *, o_domain: str = 'sync', stages: int = 2,
		async_edge: Literal['pos', 'neg'] = 'pos', max_input_delay: float | None = None
	) -> None:
		_check_stages(stages)

		if len(i) != 1:
			raise ValueError(f'AsyncFFSynchronizer input width must be 1, not {len(i)}')
		if len(o) != 1:
			raise ValueError(f'AsyncFFSynchronizer output width must be 1, not {len(o)}')

		if async_edge not in ('pos', 'neg'):
			raise ValueError(f'AsyncFFSynchronizer async edge must be one of \'pos\' or \'neg\', not {async_edge!r}')

		self.i = i
		self.o = o

		self._o_domain = o_domain
		self._stages = stages

		self._edge = async_edge

		self._max_input_delay = max_input_delay

	def elaborate(self, platform) -> Module:
		if hasattr(platform, 'get_async_ff_sync'):
			return platform.get_async_ff_sync(self)

		if self._max_input_delay is not None:
			raise NotImplementedError(
				f'Platform \'{type(platform).__name__}\' does not support constraining input delay for AsyncFFSynchronizer'
			)

		m = Module()
		m.domains += ClockDomain('async_ff', async_reset = True, local = True)
		flops = [
			Signal(1, name = f'stage{index}', reset = 1)
			for index in range(self._stages)
		]
		for i, o in zip((0, *flops), flops):
			m.d.async_ff += o.eq(i)

		if self._edge == 'pos':
			m.d.comb += ResetSignal('async_ff').eq(self.i)
		else:
			m.d.comb += ResetSignal('async_ff').eq(~self.i)

		m.d.comb += [
			ClockSignal('async_ff').eq(ClockSignal(self._o_domain)),
			self.o.eq(flops[-1])
		]

		return m

class ResetSynchronizer(Elaboratable):
	'''
	Synchronize de-assertion of a clock domain reset.

	The reset of the clock domain driven by the :class:`ResetSynchronizer` is asserted
	asynchronously and de-asserted synchronously, eliminating metastability during de-assertion.

	The driven clock domain could use a reset that is asserted either synchronously or
	asynchronously; a reset is always de-asserted synchronously. A domain with an asynchronously
	asserted reset is useful if the clock of the domain may be gated, yet the domain still
	needs to be reset promptly; otherwise, synchronously asserted reset (the default) should
	be used.

	Parameters
	----------
	arst : Signal(1), in
		Asynchronous reset signal, to be synchronized.
	domain : str
		Name of clock domain to reset.
	stages : int, >=2
		Number of synchronization stages between input and output. The lowest safe number is 2,
		with higher numbers reducing MTBF further, at the cost of increased de-assertion latency.
	max_input_delay : None or float
		Maximum delay from the input signal's clock to the first synchronization stage, in seconds.
		If specified and the platform does not support it, elaboration will fail.

	Platform overrides
	------------------
	Define the ``get_reset_sync`` platform method to override the implementation of
	:class:`ResetSynchronizer`, e.g. to instantiate library cells directly.

	'''

	def __init__(
		self, arst: Signal, *, domain: str = 'sync', stages: int = 2,
		max_input_delay: float | None = None
	) -> None:
		_check_stages(stages)

		self.arst = arst

		self._domain = domain
		self._stages = stages

		self._max_input_delay = max_input_delay

	def elaborate(self, platform) -> AsyncFFSynchronizer:
		return AsyncFFSynchronizer(
			self.arst,
			ResetSignal(self._domain),
			o_domain = self._domain,
			stages = self._stages,
			max_input_delay = self._max_input_delay
		)

class PulseSynchronizer(Elaboratable):
	'''
	A one-clock pulse on the input produces a one-clock pulse on the output.

	If the output clock is faster than the input clock, then the input may be safely asserted at
	100% duty cycle. Otherwise, if the clock ratio is ``n``:1, the input may be asserted at most
	once in every ``n`` input clocks, else pulses may be dropped. Other than this there is
	no constraint on the ratio of input and output clock frequency.

	Parameters
	----------
	i_domain : str
		Name of input clock domain.
	o_domain : str
		Name of output clock domain.
	stages : int, >=2
		Number of synchronization stages between input and output. The lowest safe number is 2,
		with higher numbers reducing MTBF further, at the cost of increased de-assertion latency.

	'''

	def __init__(self, i_domain: str, o_domain: str, *, stages: int = 2) -> None:
		_check_stages(stages)

		self.i = Signal()
		self.o = Signal()

		self._i_domain = i_domain
		self._o_domain = o_domain
		self._stages = stages

	def elaborate(self, platform) -> Module:
		m = Module()

		i_toggle = Signal()
		o_toggle = Signal()
		r_toggle = Signal()
		ff_sync = m.submodules.ff_sync = FFSynchronizer( # noqa: F841
			i_toggle, o_toggle, o_domain = self._o_domain, stages = self._stages
		)

		m.d[self._i_domain] += i_toggle.eq(i_toggle ^ self.i)
		m.d[self._o_domain] += r_toggle.eq(o_toggle)
		m.d.comb += self.o.eq(o_toggle ^ r_toggle)

		return m
