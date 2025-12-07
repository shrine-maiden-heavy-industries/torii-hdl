# SPDX-License-Identifier: BSD-2-Clause

'''

'''
from __future__     import annotations

from typing         import Generic, TypeVar

from ....build.plat import Platform
from ....hdl.ast    import Signal
from ....hdl.dsl    import Module
from ....hdl.ir     import Elaboratable
from ....hdl.xfrm   import DomainRenamer
from ...fifo        import AsyncFIFO, AsyncFIFOBuffered, SyncFIFO, SyncFIFOBuffered
from .              import StreamInterface

__all__ = (
	'StreamFIFO',
)

T = TypeVar('T', bound = StreamInterface)

class StreamFIFO(Generic[T], Elaboratable):
	'''
	A FIFO that can be inserted into the middle of a stream.

	If `domain_in` and `domain_out` are the same clock domain, then the FIFO is synchronous,
	if they are different clock domains, then the FIFO is asynchronous.

	All backpressure signaling for input and output streams are respected and derived from
	the FIFO state.

	Warning
	-------
	The StreamFIFO places some limitations on the stream which might not be desirable.

	* Only the the `data` of the stream is stored in the FIFO, any extra or ancillary
	signals are ignored.
	* The `valid` signal is collapsed down to a single bit, meaning the stream loses
	all granularity.

	Parameters
	----------
	stream_in: torii.lib.stream.StreamInterface
		The stream that will be feeding the FIFO.

	stream_out: torii.lib.stream.StreamInterface
		The stream that the FIFO will feed.

	depth: int
		How many stream records to store in the FIFO.

	domain_in: str
		The clock domain the input stream is on.

	domain_out: str
		The clock domain the output stream is on.

	buffered: bool
		If the FIFO is buffered or not.

	Attributes
	----------
	stream_in: torii.lib.stream.StreamInterface
		The input stream to read from.

	domain_in: str
		The clock domain the input stream is on.

	stream_out: torii.lib.stream.StreamInterface
		The output stream to send to.

	domain_out: str
		The clock domain the output stream is on.

	buffered: bool
		If this FIFO is buffered or not.

	depth: int
		The depth of the FIFO.

	width: int
		The width of the FIFO.

	sync: bool
		If this FIFO is synchronous or asynchronous

	in_level: Signal

	out_level: Signal
		The number of un-sent stream records.

	in_en: Signal
		Enable FIFO stream input.

		When high, ``StreamFIFO`` will operate normally and consume data from the stream. This signal
		does not override backpressure signaling.

	out_en: Signal
		Enable FIFO stream output.

		When high, ``StreamFIFO`` will operate normally and output data to the outgoing stream. This
		signal does not override backpressure signaling.
	'''

	def _select_fifo(self) -> AsyncFIFO | AsyncFIFOBuffered | SyncFIFO | SyncFIFOBuffered:
		if self.domain_in == self.domain_out:
			self.sync = True
			if self.buffered:
				return SyncFIFOBuffered(width = self.width, depth = self.depth)
			return SyncFIFO(width = self.width, depth = self.depth)

		self.sync = False

		if self.buffered:
			return AsyncFIFOBuffered(
				width = self.width, depth = self.depth,
				r_domain = self.domain_in, w_domain = self.domain_out
			)
		return AsyncFIFO(
			width = self.width, depth = self.depth,
			r_domain = self.domain_in, w_domain = self.domain_out
		)

	def __init__(
		self, stream_in: T, stream_out: T, depth: int, *,
		domain_in: str = 'sync', domain_out: str = 'sync', buffered: bool = False
	) -> None:
		self.stream_in = stream_in
		self.domain_in = domain_in

		self.stream_out = stream_out
		self.domain_out = domain_out

		self.buffered = buffered
		self.depth = depth
		self.width = len(self.stream_in.data)

		self._fifo = self._select_fifo()

		self.in_level = self._fifo.r_level
		self.out_level = self._fifo.w_level

		self.in_en = Signal()
		self.out_en = Signal()

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		# Rename the `sync` domain inside the `SyncFIFO`/`SyncFIFOBuffered` if needed
		m.submodules += DomainRenamer(sync = self.domain_in)(self._fifo) if self.sync else self._fifo

		# Input stream control
		with m.FSM(domain = self.domain_in, name = 'FIFO_RX'):
			with m.State('IDLE'):
				pass

			with m.State('RECV'):
				pass

		# Output stream control
		with m.FSM(domain = self.domain_out, name = 'FIFO_TX'):
			with m.State('IDLE'):
				pass

			with m.State('SEND'):
				pass

		return m
