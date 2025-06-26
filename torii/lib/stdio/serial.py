# SPDX-License-Identifier: BSD-2-Clause

from typing        import Literal
from warnings      import warn

from ...hdl.ast    import Signal
from ...hdl.dsl    import Cat, Const, Module
from ...hdl.ir     import Elaboratable
from ...hdl.rec    import Record
from ...util.units import bits_for
from ..cdc         import FFSynchronizer
from ..io          import Pin

__all__ = (
	'AsyncSerial',
	'AsyncSerialRX',
	'AsyncSerialTX',
)

def _check_divisor(divisor: int, bound: int):
	if divisor < bound:
		raise ValueError(f'Invalid divisor {divisor!r}; must be greater than or equal to {bound}')

def _check_parity(parity: Literal['none', 'mark', 'space', 'even', 'odd']):
	choices = ( 'none', 'mark', 'space', 'even', 'odd' )
	if parity not in choices:
		raise ValueError(f'Invalid parity {parity!r}; must be one of {", ".join(choices)}')

def _compute_parity_bit(
	data: Record , parity: Literal['none', 'mark', 'space', 'even', 'odd']
) -> Const | Record | bool:
	if parity not in ('none', 'mark', 'space', 'even', 'odd'):
		raise ValueError(f'Parity must be one of \'none\', \'mark\', \'space\', \'even\', or \'odd\', not \'{parity}\'')

	if parity == 'none':
		return Const(0, 0)
	if parity == 'mark':
		return Const(1, 1)
	if parity == 'space':
		return Const(0, 1)
	if parity == 'even':
		return data.xor()
	if parity == 'odd':
		return ~data.xor()

def _wire_layout(
	data_bits: int, parity: Literal['none', 'mark', 'space', 'even', 'odd'] = 'none'
) -> list[tuple[str, int]]:
	return [
		('start',  1),
		('data',   data_bits),
		('parity', 0 if parity == 'none' else 1),
		('stop',   1),
	]

class AsyncSerialRX(Elaboratable):
	'''
	Asynchronous serial receiver.

	Parameters
	----------
	divisor : int
		Clock divisor reset value. Should be set to ``int(clk_frequency // baudrate)``.
	divisor_bits : int
		Optional. Clock divisor width. If omitted, ``bits_for(divisor)`` is used instead.
	data_bits : int
		Data width.
	parity : ``'none'``, ``'mark'``, ``'space'``, ``'even'``, ``'odd'``
		Parity mode.
	pins : :class:`torii.lib.io.Pin`
		Optional. UART pins. See :class:`torii_boards.resources.UARTResource` for layout.

	Attributes
	----------
	divisor : Signal, in
		Clock divisor.
	data : Signal, out
		Read data. Valid only when ``rdy`` is asserted.
	err.overflow : Signal, out
		Error flag. A new frame has been received, but the previous one was not acknowledged.
	err.frame : Signal, out
		Error flag. The received bits do not fit in a frame.
	err.parity : Signal, out
		Error flag. The parity check has failed.
	rdy : Signal, out
		Read strobe. (deprecated, use `done`)
	ack : Signal, in
		Read acknowledge. Must be held asserted while data can be read out of the receiver. (deprecated use `start`)
	done : Signal, out
		Strobe that indicates we successfully completed receiving a frame of data.
	start : Signal, in
		Indication from the driving gateware that it is interested in new data from the receiver.
		Must be held asserted to indicate reception is okay.
	i : Signal, in
		Serial input. If ``pins`` has been specified, ``pins.rx.i`` drives it.

	'''

	def __init__(
		self, *, divisor: int, divisor_bits: int | None = None, data_bits: int = 8,
		parity: Literal['none', 'mark', 'space', 'even', 'odd'] = 'none',
		pins: Pin | None = None
	) -> None:
		_check_parity(parity)
		self._parity = parity

		# The clock divisor must be at least 5 to keep the FSM synchronized with the serial input
		# during a DONE->IDLE->BUSY transition.
		_check_divisor(divisor, 5)
		self.divisor = Signal(divisor_bits or bits_for(divisor), reset = divisor)

		self.data = Signal(data_bits)
		self.err  = Record([
			('overflow', 1),
			('frame',    1),
			('parity',   1),
		])
		self.done  = Signal()
		self.start = Signal()

		self.i    = Signal(reset = 1)

		self._pins = pins

	def __getattr__(self, name: str):

		# Re-map the `rdy` alias to `done`
		if name == 'rdy':
			warn(
				'AsyncSerialRX `rdy` signal is deprecated, please use `done` instead\n',
				DeprecationWarning,
				stacklevel = 2
			)
			name = 'done'
		elif name == 'ack':
			warn(
				'AsyncSerialRX `ack` signal is deprecated, please use `start` instead\n',
				DeprecationWarning,
				stacklevel = 2
			)
			name = 'start'

		return super().__getattr__(name)

	def elaborate(self, platform) -> Module:
		m = Module()

		timer = Signal.like(self.divisor)
		shreg = Record(_wire_layout(len(self.data), self._parity))
		bitno = Signal(range(len(shreg)))

		if self._pins is not None:
			m.submodules += FFSynchronizer(self._pins.rx.i, self.i, reset = 1)

		# TODO: This has some really messed up behaviour with how the start/done bits work - this FSM
		# needs a internals rewrite, but this can't be done till we are able to make breaking changes
		# (prep for v1.0.0). `self.start` should be latched at the start of the frame or while busy
		# so it can be a pulse from the driving block, rather than having to remain asserted all the way
		# through to 'DONE'.
		with m.FSM() as fsm:
			with m.State('IDLE'):
				with m.If(~self.i):
					m.d.sync += [
						bitno.eq(len(shreg) - 1),
						timer.eq(self.divisor >> 1),
					]
					m.next = 'BUSY'

			with m.State('BUSY'):
				with m.If(timer != 0):
					m.d.sync += timer.eq(timer - 1)
				with m.Else():
					m.d.sync += [
						shreg.eq(Cat(shreg[1:], self.i)),
						bitno.eq(bitno - 1),
						timer.eq(self.divisor - 1),
					]
					with m.If(bitno == 0):
						m.next = 'DONE'

			with m.State('DONE'):
				with m.If(self.start):
					m.d.sync += [
						self.data.eq(shreg.data),
						self.err.frame .eq(~((shreg.start == 0) & (shreg.stop == 1))),
						self.err.parity.eq(~(
							shreg.parity == _compute_parity_bit(shreg.data, self._parity)
						)),
					]
				m.d.sync += self.err.overflow.eq(~self.start)
				m.next = 'IDLE'

		with m.If(self.start):
			m.d.sync += self.done.eq(fsm.ongoing('DONE'))

		return m

class AsyncSerialTX(Elaboratable):
	'''
	Asynchronous serial transmitter.

	Parameters
	----------
	divisor : int
		Clock divisor reset value. Should be set to ``int(clk_frequency // baudrate)``.
	divisor_bits : int
		Optional. Clock divisor width. If omitted, ``bits_for(divisor)`` is used instead.
	data_bits : int
		Data width.
	parity : ``'none'``, ``'mark'``, ``'space'``, ``'even'``, ``'odd'``
		Parity mode.
	pins : :class:`torii.lib.io.Pin`
		Optional. UART pins. See :class:`torii_boards.resources.UARTResource` for layout.

	Attributes
	----------
	divisor : Signal, in
		Clock divisor.
	data : Signal, in
		Write data. Valid only when ``ack`` is asserted.
	rdy : Signal, out
		Write ready. Asserted when the transmitter is ready to transmit data.
	ack : Signal, in
		Write strobe. Data gets transmitted when both ``rdy`` and ``ack`` are asserted.
	o : Signal, out
		Serial output. If ``pins`` has been specified, it drives ``pins.tx.o``.

	'''

	def __init__(
		self, *, divisor: int, divisor_bits: int | None = None, data_bits: int = 8,
		parity  : Literal['none', 'mark', 'space', 'even', 'odd'] = 'none',
		pins: Pin | None = None
	) -> None:
		_check_parity(parity)
		self._parity = parity

		_check_divisor(divisor, 1)
		self.divisor = Signal(divisor_bits or bits_for(divisor), reset = divisor)

		self.data = Signal(data_bits)
		self.rdy  = Signal()
		self.ack  = Signal()

		self.o    = Signal(reset = 1)

		self._pins = pins

	def elaborate(self, platform) -> Module:
		m = Module()

		timer = Signal.like(self.divisor)
		shreg = Record(_wire_layout(len(self.data), self._parity))
		bitno = Signal(range(len(shreg)))

		if self._pins is not None:
			m.d.comb += self._pins.tx.o.eq(self.o)

		with m.FSM():
			with m.State('IDLE'):
				m.d.comb += self.rdy.eq(1)
				with m.If(self.ack):
					m.d.sync += [
						shreg.start .eq(0),
						shreg.data  .eq(self.data),
						shreg.parity.eq(_compute_parity_bit(self.data, self._parity)),
						shreg.stop  .eq(1),
						bitno.eq(len(shreg) - 1),
						timer.eq(self.divisor - 1),
					]
					m.next = 'BUSY'

			with m.State('BUSY'):
				with m.If(timer != 0):
					m.d.sync += timer.eq(timer - 1)
				with m.Else():
					m.d.sync += [
						Cat(self.o, shreg).eq(shreg),
						bitno.eq(bitno - 1),
						timer.eq(self.divisor - 1),
					]
					with m.If(bitno == 0):
						m.next = 'IDLE'

		return m

class AsyncSerial(Elaboratable):
	'''
	Asynchronous serial transceiver.

	Parameters
	----------
	divisor : int
		Clock divisor reset value. Should be set to ``int(clk_frequency // baudrate)``.
	divisor_bits : int
		Optional. Clock divisor width. If omitted, ``bits_for(divisor)`` is used instead.
	data_bits : int
		Data width.
	parity : ``'none'``, ``'mark'``, ``'space'``, ``'even'``, ``'odd'``
		Parity mode.
	pins : :class:`torii.lib.io.Pin`
		Optional. UART pins. See :class:`torii_boards.resources.UARTResource` for layout.

	Attributes
	----------
	divisor : Signal, in
		Clock divisor.
	rx : :class:`AsyncSerialRX`
		See :class:`AsyncSerialRX`.
	tx : :class:`AsyncSerialTX`
		See :class:`AsyncSerialTX`.

	'''

	def __init__(
		self, *, divisor: int, divisor_bits: int | None = None, **kwargs
	) -> None:
		self.divisor = Signal(divisor_bits or bits_for(divisor), reset = divisor)

		self.rx = AsyncSerialRX(divisor = divisor, divisor_bits = divisor_bits, **kwargs)
		self.tx = AsyncSerialTX(divisor = divisor, divisor_bits = divisor_bits, **kwargs)

	def elaborate(self, platform) -> Module:
		m = Module()
		m.submodules.rx = self.rx
		m.submodules.tx = self.tx
		m.d.comb += [
			self.rx.divisor.eq(self.divisor),
			self.tx.divisor.eq(self.divisor),
		]
		return m
