# SPDX-License-Identifier: BSD-2-Clause

''' First-in first-out queues. '''

from __future__   import annotations

from ..hdl.ast    import Mux, ResetSignal, Signal
from ..hdl.dsl    import Module
from ..hdl.ir     import Elaboratable
from ..hdl.mem    import Memory
from ..util.units import log2_ceil
from .cdc         import AsyncFFSynchronizer, FFSynchronizer
from .coding.gray import Decoder, Encoder
from .formal      import Assert, Assume, Initial

__all__ = (
	'AsyncFIFO',
	'AsyncFIFOBuffered',
	'FIFOInterface',
	'SyncFIFO',
	'SyncFIFOBuffered',
)

_DOC_TEMPLATE = {
	'parameters': '''
	width : int
		Bit width of data entries.
	depth : int
		Depth of the queue. If zero, the FIFO cannot be read from or written to.
	''',
	'w_attributes': '''
	w_data : Signal(width), in
		Input data.
	w_rdy : Signal(1), out
		Asserted if there is space in the queue, i.e. ``w_en`` can be asserted to write
		a new entry.
	w_en : Signal(1), in
		Write strobe. Latches ``w_data`` into the queue. Does nothing if ``w_rdy`` is not asserted.
	w_level : Signal(range(depth + 1)), out
		Number of unread entries.
	''',
	'r_attributes': '''
	r_data : Signal(width), out
		Output data. {r_data_valid}
	r_rdy : Signal(1), out
		Asserted if there is an entry in the queue, i.e. ``r_en`` can be asserted to read
		an existing entry.
	r_en : Signal(1), in
		Read strobe. Makes the next entry (if any) available on ``r_data`` at the next cycle.
		Does nothing if ``r_rdy`` is not asserted.
	r_level : Signal(range(depth + 1)), out
		Number of unread entries.
	''',
}


class FIFOInterface:
	__doc__ = '''
	Data written to the input interface (``w_data``, ``w_rdy``, ``w_en``) is buffered and can be
	read at the output interface (``r_data``, ``r_rdy``, ``r_en``). The data entry written first
	to the input also appears first on the output.

	Parameters
	----------
	{parameters}
	fwft : bool
		First-word fallthrough. If set, when ``r_rdy`` rises, the first entry is already
		available, i.e. ``r_data`` is valid. Otherwise, after ``r_rdy`` rises, it is necessary
		to strobe ``r_en`` for ``r_data`` to become valid.

	Attributes
	----------
	{w_attributes}
	{r_attributes}
	'''.format(
		parameters = _DOC_TEMPLATE['parameters'].strip().strip(),
		w_attributes = _DOC_TEMPLATE['w_attributes'].strip().strip(),
		r_attributes = _DOC_TEMPLATE['r_attributes'].strip().strip().format(
			r_data_valid = 'The conditions in which ``r_data`` is valid depends on the type of the queue.'
		),
	)

	def __init__(self, *, width: int, depth: int, fwft: bool = True) -> None:
		if not isinstance(width, int) or width < 0:
			raise TypeError(f'FIFO width must be a non-negative integer, not {width!r}')

		if not isinstance(depth, int) or depth < 0:
			raise TypeError(f'FIFO depth must be a non-negative integer, not {depth!r}')

		self.width = width
		self.depth = depth
		self.fwft  = fwft

		self.w_data = Signal(width, reset_less = True)
		self.w_rdy  = Signal() # writable; not full
		self.w_en   = Signal()
		self.w_level = Signal(range(depth + 1))

		self.r_data = Signal(width, reset_less = True)
		self.r_rdy  = Signal() # readable; not empty
		self.r_en   = Signal()
		self.r_level = Signal(range(depth + 1))

def _incr(signal, modulo: int) -> Mux | int:
	if modulo == 2 ** len(signal):
		return signal + 1
	else:
		return Mux(signal == modulo - 1, 0, signal + 1)

class SyncFIFO(Elaboratable, FIFOInterface):
	__doc__ = '''
	Synchronous first in, first out queue.

	Read and write interfaces are accessed from the same clock domain. If different clock domains
	are needed, use :class:`AsyncFIFO`.

	Parameters
	----------
	{parameters}
	fwft : bool
		First-word fallthrough. If set, when the queue is empty and an entry is written into it,
		that entry becomes available on the output on the same clock cycle. Otherwise, it is
		necessary to assert ``r_en`` for ``r_data`` to become valid.

	Attributes
	----------
	level : Signal(range(depth + 1)), out
		Number of unread entries. This level is the same between read and write for synchronous FIFOs.
	{w_attributes}
	{r_attributes}
	'''.format(
		parameters = _DOC_TEMPLATE['parameters'].strip(),
		w_attributes = _DOC_TEMPLATE['w_attributes'].strip(),
		r_attributes = _DOC_TEMPLATE['r_attributes'].strip().format(
			r_data_valid = 'For FWFT queues, valid if ``r_rdy`` is asserted. '
			'For non-FWFT queues, valid on the next cycle after ``r_rdy`` and ``r_en`` have been asserted.'
		),
	)

	def __init__(self, *, width: int, depth: int, fwft: bool = True) -> None:
		super().__init__(width = width, depth = depth, fwft = fwft)

		self.level = Signal(range(depth + 1))

	def elaborate(self, platform) -> Module:
		m = Module()
		if self.depth == 0:
			m.d.comb += [
				self.w_rdy.eq(0),
				self.r_rdy.eq(0),
			]
			return m

		m.d.comb += [
			self.w_rdy.eq(self.level != self.depth),
			self.r_rdy.eq(self.level != 0),
			self.w_level.eq(self.level),
			self.r_level.eq(self.level),
		]

		do_read  = self.r_rdy & self.r_en
		do_write = self.w_rdy & self.w_en

		m.submodules.storage = storage = Memory(width = self.width, depth = self.depth)
		w_port = storage.write_port()
		r_port = storage.read_port(
			domain = 'comb' if self.fwft else 'sync', transparent = self.fwft)
		produce = Signal(range(self.depth))
		consume = Signal(range(self.depth))

		m.d.comb += [
			w_port.addr.eq(produce),
			w_port.data.eq(self.w_data),
			w_port.en.eq(self.w_en & self.w_rdy),
		]
		with m.If(do_write):
			m.d.sync += produce.eq(_incr(produce, self.depth))

		m.d.comb += [
			r_port.addr.eq(consume),
			self.r_data.eq(r_port.data),
		]
		if not self.fwft:
			m.d.comb += r_port.en.eq(self.r_en)
		with m.If(do_read):
			m.d.sync += consume.eq(_incr(consume, self.depth))

		with m.If(do_write & ~do_read):
			m.d.sync += self.level.eq(self.level + 1)
		with m.If(do_read & ~do_write):
			m.d.sync += self.level.eq(self.level - 1)

		if platform == 'formal':
			# TODO: move this logic to SymbiYosys
			with m.If(Initial()):
				m.d.comb += [
					Assume(produce < self.depth),
					Assume(consume < self.depth),
				]
				with m.If(produce == consume):
					m.d.comb += Assume((self.level == 0) | (self.level == self.depth))
				with m.If(produce > consume):
					m.d.comb += Assume(self.level == (produce - consume))
				with m.If(produce < consume):
					m.d.comb += Assume(self.level == (self.depth + produce - consume))
			with m.Else():
				m.d.comb += [
					Assert(produce < self.depth),
					Assert(consume < self.depth),
				]
				with m.If(produce == consume):
					m.d.comb += Assert((self.level == 0) | (self.level == self.depth))
				with m.If(produce > consume):
					m.d.comb += Assert(self.level == (produce - consume))
				with m.If(produce < consume):
					m.d.comb += Assert(self.level == (self.depth + produce - consume))

		return m

class SyncFIFOBuffered(Elaboratable, FIFOInterface):
	__doc__ = '''
	Buffered synchronous first in, first out queue.

	This queue's interface is identical to :class:`SyncFIFO` configured as ``fwft = True``, but it
	does not use asynchronous memory reads, which are incompatible with FPGA block RAMs.

	In exchange, the latency between an entry being written to an empty queue and that entry
	becoming available on the output is increased by one cycle compared to :class:`SyncFIFO`.

	Parameters
	----------
	{parameters}
	fwft : bool
		Always set.

	Attributes
	----------
	level : Signal(range(depth + 1)), out
		Number of unread entries. This level is the same between read and write for synchronous FIFOs.
	{w_attributes}
	{r_attributes}
	'''.format(
		parameters = _DOC_TEMPLATE['parameters'].strip(),
		w_attributes = _DOC_TEMPLATE['w_attributes'].strip(),
		r_attributes = _DOC_TEMPLATE['r_attributes'].strip().format(
			r_data_valid = 'Valid if ``r_rdy`` is asserted.'
		),
	)

	def __init__(self, *, width: int, depth: int) -> None:
		super().__init__(width = width, depth = depth)

		self.level = Signal(range(depth + 1))

	def elaborate(self, platform) -> Module:
		m = Module()
		if self.depth == 0:
			m.d.comb += [
				self.w_rdy.eq(0),
				self.r_rdy.eq(0),
			]
			return m

		# Effectively, this queue treats the output register of the non-FWFT inner queue as
		# an additional storage element.
		m.submodules.unbuffered = fifo = SyncFIFO(
			width = self.width,
			depth = self.depth - 1,
			fwft = False
		)

		m.d.comb += [
			fifo.w_data.eq(self.w_data),
			fifo.w_en.eq(self.w_en),
			self.w_rdy.eq(fifo.w_rdy),
		]

		m.d.comb += [
			self.r_data.eq(fifo.r_data),
			fifo.r_en.eq(fifo.r_rdy & (~self.r_rdy | self.r_en)),
		]
		with m.If(fifo.r_en):
			m.d.sync += self.r_rdy.eq(1)
		with m.Elif(self.r_en):
			m.d.sync += self.r_rdy.eq(0)

		m.d.comb += [
			self.level.eq(fifo.level + self.r_rdy),
			self.w_level.eq(self.level),
			self.r_level.eq(self.level),
		]

		return m

class AsyncFIFO(Elaboratable, FIFOInterface):
	__doc__ = '''
	Asynchronous first in, first out queue.

	Read and write interfaces are accessed from different clock domains, which can be set when
	constructing the FIFO.

	:class:`AsyncFIFO` can be reset from the write clock domain. When the write domain reset is
	asserted, the FIFO becomes empty. When the read domain is reset, data remains in the FIFO - the
	read domain logic should correctly handle this case.

	:class:`AsyncFIFO` only supports power of 2 depths. Unless ``exact_depth`` is specified,
	the ``depth`` parameter is rounded up to the next power of 2.

	Parameters
	----------
	{parameters}
	r_domain : str
		Read clock domain.
	w_domain : str
		Write clock domain.
	fwft : bool
		Always set.

	Attributes
	----------
	{w_attributes}
	{r_attributes}
	r_rst : Signal(1), out
		Asserted, for at least one read-domain clock cycle, after the FIFO has been reset by
		the write-domain reset.
	'''.format(
		parameters = _DOC_TEMPLATE['parameters'].strip(),
		w_attributes = _DOC_TEMPLATE['w_attributes'].strip(),
		r_attributes = _DOC_TEMPLATE['r_attributes'].strip().format(
			r_data_valid = 'Valid if ``r_rdy`` is asserted.'
		),
	)

	def __init__(
		self, *, width: int, depth: int, r_domain: str = 'read', w_domain: str = 'write',
		exact_depth: bool = False
	) -> None:
		if depth != 0:
			depth_bits = log2_ceil(depth)
			if exact_depth and depth != 1 << depth_bits:
				raise ValueError(
					f'AsyncFIFO only supports depths that are powers of 2; requested exact depth {depth} is not'
				) from None
			depth = 1 << depth_bits
		else:
			depth_bits = 0
		super().__init__(width = width, depth = depth)

		self.r_rst = Signal()
		self._r_domain = r_domain
		self._w_domain = w_domain
		self._ctr_bits = depth_bits + 1

	def elaborate(self, platform) -> Module:
		m = Module()
		if self.depth == 0:
			m.d.comb += [
				self.w_rdy.eq(0),
				self.r_rdy.eq(0),
			]
			return m

		# The design of this queue is the "style #2" from Clifford E. Cummings' paper "Simulation
		# and Synthesis Techniques for Asynchronous FIFO Design":
		# http://www.sunburst-design.com/papers/CummingsSNUG2002SJ_FIFO1.pdf

		do_write = self.w_rdy & self.w_en
		do_read  = self.r_rdy & self.r_en

		# TODO: extract this pattern into lib.cdc.GrayCounter
		produce_w_bin = Signal(self._ctr_bits)
		produce_w_nxt = Signal(self._ctr_bits)
		m.d.comb += produce_w_nxt.eq(produce_w_bin + do_write)
		m.d[self._w_domain] += produce_w_bin.eq(produce_w_nxt)

		# Note: Both read-domain counters must be reset_less (see comments below)
		consume_r_bin = Signal(self._ctr_bits, reset_less = True)
		consume_r_nxt = Signal(self._ctr_bits)
		m.d.comb += consume_r_nxt.eq(consume_r_bin + do_read)
		m.d[self._r_domain] += consume_r_bin.eq(consume_r_nxt)

		produce_w_gry = Signal(self._ctr_bits)
		produce_r_gry = Signal(self._ctr_bits)
		produce_enc = m.submodules.produce_enc = Encoder(self._ctr_bits)
		produce_cdc = m.submodules.produce_cdc = FFSynchronizer(  # noqa: F841
			produce_w_gry, produce_r_gry, o_domain = self._r_domain
		)
		m.d.comb += produce_enc.i.eq(produce_w_nxt),
		m.d[self._w_domain] += produce_w_gry.eq(produce_enc.o)

		consume_r_gry = Signal(self._ctr_bits, reset_less = True)
		consume_w_gry = Signal(self._ctr_bits)
		consume_enc = m.submodules.consume_enc = Encoder(self._ctr_bits)
		consume_cdc = m.submodules.consume_cdc = FFSynchronizer(  # noqa: F841
			consume_r_gry, consume_w_gry, o_domain = self._w_domain
		)
		m.d.comb += consume_enc.i.eq(consume_r_nxt)
		m.d[self._r_domain] += consume_r_gry.eq(consume_enc.o)

		consume_w_bin = Signal(self._ctr_bits)
		consume_dec = m.submodules.consume_dec = Decoder(self._ctr_bits)
		m.d.comb += consume_dec.i.eq(consume_w_gry),
		m.d[self._w_domain] += consume_w_bin.eq(consume_dec.o)

		produce_r_bin = Signal(self._ctr_bits)
		produce_dec = m.submodules.produce_dec = Decoder(self._ctr_bits)
		m.d.comb += produce_dec.i.eq(produce_r_gry),
		m.d.comb += produce_r_bin.eq(produce_dec.o)

		w_full  = Signal()
		r_empty = Signal()
		m.d.comb += [
			w_full.eq(
				(produce_w_gry[-1]  != consume_w_gry[-1]) &
				(produce_w_gry[-2]  != consume_w_gry[-2]) &
				(produce_w_gry[:-2] == consume_w_gry[:-2])
			),
			r_empty.eq(consume_r_gry == produce_r_gry),
		]

		m.d[self._w_domain] += self.w_level.eq(produce_w_bin - consume_w_bin)
		m.d.comb += self.r_level.eq(produce_r_bin - consume_r_bin)

		m.submodules.storage = storage = Memory(width = self.width, depth = self.depth)
		w_port = storage.write_port(domain = self._w_domain)
		r_port = storage.read_port(
			domain = self._r_domain, transparent = False
		)
		m.d.comb += [
			w_port.addr.eq(produce_w_bin[:-1]),
			w_port.data.eq(self.w_data),
			w_port.en.eq(do_write),
			self.w_rdy.eq(~w_full),
		]
		m.d.comb += [
			r_port.addr.eq(consume_r_nxt[:-1]),
			self.r_data.eq(r_port.data),
			r_port.en.eq(1),
			self.r_rdy.eq(~r_empty),
		]

		# Reset handling to maintain FIFO and CDC invariants in the presence of a write-domain
		# reset.
		# There is a CDC hazard associated with resetting an async FIFO - Gray code counters which
		# are reset to 0 violate their Gray code invariant. One way to handle this is to ensure
		# that both sides of the FIFO are asynchronously reset by the same signal. We adopt a
		# slight variation on this approach - reset control rests entirely with the write domain.
		# The write domain's reset signal is used to asynchronously reset the read domain's
		# counters and force the FIFO to be empty when the write domain's reset is asserted.
		# This requires the two read domain counters to be marked as "reset_less", as they are
		# reset through another mechanism. See https://github.com/amaranth-lang/amaranth/issues/181
		# for the full discussion.
		w_rst = ResetSignal(domain = self._w_domain, allow_reset_less = True)
		r_rst = Signal()

		# Async-set-sync-release synchronizer avoids CDC hazards
		rst_cdc = m.submodules.rst_cdc = AsyncFFSynchronizer(w_rst, r_rst, o_domain = self._r_domain)  # noqa: F841

		# Decode Gray code counter synchronized from write domain to overwrite binary
		# counter in read domain.
		rst_dec = m.submodules.rst_dec = Decoder(self._ctr_bits)
		m.d.comb += rst_dec.i.eq(produce_r_gry)
		with m.If(r_rst):
			m.d.comb += r_empty.eq(1)
			m.d[self._r_domain] += consume_r_gry.eq(produce_r_gry)
			m.d[self._r_domain] += consume_r_bin.eq(rst_dec.o)
			m.d[self._r_domain] += self.r_rst.eq(1)
		with m.Else():
			m.d[self._r_domain] += self.r_rst.eq(0)

		if platform == 'formal':
			with m.If(Initial()):
				m.d.comb += Assume(produce_w_gry == (produce_w_bin ^ produce_w_bin[1:]))
				m.d.comb += Assume(consume_r_gry == (consume_r_bin ^ consume_r_bin[1:]))

		return m

class AsyncFIFOBuffered(Elaboratable, FIFOInterface):
	__doc__ = '''
	Buffered asynchronous first in, first out queue.

	Read and write interfaces are accessed from different clock domains, which can be set when
	constructing the FIFO.

	:class:`AsyncFIFOBuffered` only supports power of 2 plus one depths. Unless ``exact_depth``
	is specified, the ``depth`` parameter is rounded up to the next power of 2 plus one.
	(The output buffer acts as an additional queue element.)

	This queue's interface is identical to :class:`AsyncFIFO`, but it has an additional register
	on the output, improving timing in case of block RAM that has large clock-to-output delay.

	In exchange, the latency between an entry being written to an empty queue and that entry
	becoming available on the output is increased by one cycle compared to :class:`AsyncFIFO`.

	Parameters
	----------
	{parameters}
	r_domain : str
		Read clock domain.
	w_domain : str
		Write clock domain.
	fwft : bool
		Always set.

	Attributes
	----------
	{w_attributes}
	{r_attributes}
	r_rst : Signal(1), out
		Asserted, for at least one read-domain clock cycle, after the FIFO has been reset by
		the write-domain reset.
	'''.format(
		parameters = _DOC_TEMPLATE['parameters'].strip(),
		w_attributes = _DOC_TEMPLATE['w_attributes'].strip(),
		r_attributes = _DOC_TEMPLATE['r_attributes'].strip().format(
			r_data_valid = 'Valid if ``r_rdy`` is asserted.'
		),
	)

	def __init__(
		self, *, width: int, depth: int, r_domain: str = 'read', w_domain: str = 'write',
		exact_depth: bool = False
	) -> None:
		if depth != 0:
			depth_bits = log2_ceil(max(0, depth - 1))
			if exact_depth and depth != (1 << depth_bits) + 1:
				raise ValueError(
					'AsyncFIFOBuffered only supports depths that are one higher than powers of 2; '
					f'requested exact depth {depth} is not'
				) from None
			depth = (1 << depth_bits) + 1

		super().__init__(width = width, depth = depth)

		self.r_rst = Signal()
		self._r_domain = r_domain
		self._w_domain = w_domain

	def elaborate(self, platform) -> Module:
		m = Module()
		if self.depth == 0:
			m.d.comb += [
				self.w_rdy.eq(0),
				self.r_rdy.eq(0),
			]
			return m

		m.submodules.unbuffered = fifo = AsyncFIFO(
			width = self.width,
			depth = self.depth - 1,
			r_domain = self._r_domain,
			w_domain = self._w_domain
		)

		m.d.comb += [
			fifo.w_data.eq(self.w_data),
			self.w_rdy.eq(fifo.w_rdy),
			fifo.w_en.eq(self.w_en),
		]

		r_consume_buffered = Signal()
		m.d.comb += r_consume_buffered.eq((self.r_rdy - self.r_en) & self.r_rdy)
		m.d[self._r_domain] += self.r_level.eq(fifo.r_level + r_consume_buffered)

		w_consume_buffered = Signal()
		m.submodules.consume_buffered_cdc = FFSynchronizer(
			r_consume_buffered, w_consume_buffered, o_domain = self._w_domain, stages = 4
		)
		m.d.comb += self.w_level.eq(fifo.w_level + w_consume_buffered)

		with m.If(self.r_en | ~self.r_rdy):
			m.d[self._r_domain] += [
				self.r_data.eq(fifo.r_data),
				self.r_rdy.eq(fifo.r_rdy),
				self.r_rst.eq(fifo.r_rst),
			]
			m.d.comb += [
				fifo.r_en.eq(1)
			]

		return m
