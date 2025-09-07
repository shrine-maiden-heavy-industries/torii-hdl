# SPDX-License-Identifier: BSD-2-Clause

'''

'''

from __future__      import annotations

from collections.abc import Sequence
from typing          import TypeAlias, Literal, Generic, TypeVar

from torii.build.plat import Platform

from .               import StreamInterface
from ....hdl.ast     import Array, Const, Signal
from ....hdl.dsl     import Module
from ....hdl.ir      import Elaboratable
from ....hdl.mem     import Memory
from ....hdl.xfrm    import DomainRenamer

ConstData: TypeAlias = bytes | bytearray | Sequence[int]

T = TypeVar('T', bound = StreamInterface)

class ConstantStreamGenerator(Generic[T], Elaboratable):
	'''
	A simple stream generator that constantly outputs fixed data into a receiving stream.

	Parameters
	----------
	data: ConstData
		The constant data to be emitted from the stream.

	data_width: int | None = None
		The width in bits of ``data``. If not provided it will be taken from the ``StreamInterface``s width.
		(default: None)

	max_length_width: int | None
		If provided, a ``max_length_width`` signal will be present that can limit the total length transmitted.
		(default: None)

	endianness: Literal['big', 'little']
		If ``data`` is a bytes-like object, and ``data_width`` is more than 8 bits.
		(default: 'little')

	stream_type: type
		The type of stream to create, must be either :py:class:`StreamInterface <torii.lib.stream.StreamInterface>`
		or a subtype there of.
		(default: torii.lib.stream.StreamInterface)

	domain: str
		The clock domain in which the stream generator should be clocked.
		(default: 'sync')

	Attributes
	----------
	start: Signal, in
		Input strobe to start the stream

	done: Signal, out
		Output strobe indicating the transmission is completed

	start_pos: Signal(range(len(data))), in
		The starting position within ``data``. Latched when ``start`` is strobed.

	max_length: Signal(max_length_width), in
		The maximum length of ``data`` to be sent in bytes.
		Must be >= ``len(data)``.
		By default this value is the length of ``data``.

	out_length: Signal(max_length_width), out
		Indicates the the total amount of data that has streamed out.
		Will always be less than ``max_len``.

	stream: stream_type, out
		The output data stream.
	'''

	def __init__(
		self, data: ConstData, data_width: int | None = None, max_length_width: int | None = None,
		endianness: Literal['big', 'little'] = 'little', stream_type: type[T] = StreamInterface, domain: str = 'sync'
	) -> None:
		self._domain           = domain
		self._data             = data
		self._len              = len(self._data)
		self._endian           = endianness
		self._max_length_width = max_length_width

		self.start     = Signal()
		self.done      = Signal()
		self.start_pos = Signal(range(self._len))

		if data_width:
			self.stream      = stream_type(data_width = data_width)
			self._data_width = data_width
		else:
			self.stream      = stream_type()
			self._data_width = len(self.stream.data)

		if max_length_width:
			self.max_len    = Signal(max_length_width)
			self.out_length = Signal.like(self.max_len)
		else:
			self.max_len = Const(self._len)
			self.out_length = Const(self._len)

	def _get_initializer_value(self):
		'''
		Returns the data for this generator in a form that is appropriate for ROM initialization.

		Returns
		-------
		tuple[Iterable[int], int]
			A tuple containing an iterable of the data for ROM initialization and the number of slack bits
			for the last value.
		'''

		# If we are using 8-bit bytes, then we don't need to massage the data
		if self._data_width == 8:
			return (self._data, len(self.stream.valid), )

		# If it's not a bytes-like object, then do the same
		if not isinstance(self._data, (bytes, bytearray)):
			return (self._data, len(self.stream.valid), )

		# If the width of data is not divisible by 8, then we cant ingest bytes
		if self._data_width % 8:
			raise ValueError('Unable to initialize bytes with data width not divisible by 8')

		# Get the byte width for out data
		data_bytes = self._data_width // 8

		init_data = bytearray(self._data)
		result_data: list[int] = []

		while init_data:
			dat = init_data[0:data_bytes]
			del init_data[0:data_bytes]

			result_data.append(int.from_bytes(dat, byteorder = self._endian))

		last_bytes = len(self._data) % data_bytes
		if last_bytes == 0:
			last_bytes = data_bytes

		return (result_data, last_bytes, )

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		# Source ROM
		data, slack_bits = self._get_initializer_value()
		data_len = len(data)

		rom = Memory(width = self._data_width, depth = data_len, init = data)
		m.submodules.read_port = read_port = rom.read_port(transparent = False)

		if self._max_length_width:
			max_len = Signal(self.max_len.shape())
		else:
			max_len = self.max_len

		stream_pos = Signal(range(data_len))

		if self._max_length_width:
			bytes_sent     = Signal(self._max_length_width)
			bytes_per_word = (self._data_width + 7) // 8
		else:
			bytes_sent     = Signal(0)
			bytes_per_word = 0

		on_first = stream_pos == self.start_pos
		on_last  = (stream_pos == data_len - 1) | (bytes_sent + bytes_per_word >= max_len)

		start_pos = Signal.like(stream_pos)

		with m.If(self.start_pos >= self._len):
			m.d.comb += [ start_pos.eq(data_len - 1), ]
		with m.Else():
			m.d.comb += [ start_pos.eq(self.start_pos), ]

		if self._max_length_width:
			with m.If(max_len < self._len):
				m.d.comb += [ self.out_length.eq(max_len), ]
			with m.Else():
				m.d.comb += [ self.out_length.eq(self._len), ]

		with m.FSM(domain = self._domain) as fsm:
			m.d.comb += [ self.stream.valid.eq(fsm.ongoing('STREAMING')), ]

			with m.State('IDLE'):
				m.d.sync += [
					stream_pos.eq(start_pos),
					bytes_sent.eq(0),
				]

				m.d.comb += [ read_port.addr.eq(start_pos), ]

				m.d.sync += [ max_len.eq(self.max_len), ]

				with m.If(self.start & (self.max_len > 0)):
					m.next = 'STREAMING'

			with m.State('STREAMING'):
				m.d.comb += [
					read_port.addr.eq(stream_pos),
					self.stream.data.eq(read_port.data),
					self.stream.first.eq(on_first),
					self.stream.last.eq(on_last),
				]

				if len(self.stream.valid) == 1:
					m.d.comb += [ self.stream.valid.eq(1), ]
				else:
					with m.If(on_last):
						if not self._max_length_width:
							m.d.comb += [ self.stream.valid.eq(Const(1).replicate(slack_bits)), ]
						else:
							end_data_len = (stream_pos == (data_len - 1))
							end_max_len  = (bytes_sent + bytes_per_word >= max_len)
							valid_slack  = Const(1).replicate(slack_bits)

							leftover_bytes = Signal(range(bytes_per_word + 1))
							valid_max_len  = Signal.like(self.stream.valid)

							m.d.comb += [
								leftover_bytes.eq(max_len - bytes_sent),
							]

							with m.Switch(leftover_bytes):
								for bits in range(1, bytes_per_word + 1):
									with m.Case(bits):
										m.d.comb += [ valid_max_len.eq(Const(1).replicate(bits)) ]

							with m.If(end_data_len & end_max_len):
								m.d.comb += [ self.stream.valid.eq(valid_slack & valid_max_len), ]
							with m.Elif(end_data_len):
								m.d.comb += [ self.stream.valid.eq(valid_slack), ]
							with m.Else():
								m.d.comb += [ self.stream.valid.eq(valid_max_len), ]

					with m.Else():
						valid_bits = len(self.stream.valid)
						m.d.comb += [ self.stream.valid.eq(Const(1).replicate(valid_bits)), ]

				with m.If(self.stream.ready):
					with m.If(~on_last):
						m.d.sync += [ stream_pos.inc(), ]
						m.d.comb += [ read_port.addr.eq(stream_pos + 1), ]

						if self._max_length_width:
							m.d.sync += [ bytes_sent.inc(bytes_per_word), ]
					with m.Else():
						m.next = 'DONE'

			with m.State('DONE'):
				m.d.comb += [ self.done.eq(1), ]
				m.next = 'IDLE'

		if self._domain != 'sync':
			m = DomainRenamer(sync = self._domain)(m)
		return m

class StreamSerializer(Generic[T], Elaboratable):
	'''
	Serialize a small chunk of data into the given stream.

	Parameters
	----------
	data_length: int
		The length of the data to be serialized and transmitted.

	domain: str
		The clock domain this generator operates on.

	data_width: int
		The width of the constant payload.

	stream_type: type[T]
		The type of stream used, must be a :py:class:`SimpleStream` or subclass thereof.

	max_len_width: int | None
		If provided, the width of the `max_len` signal.

	Attributes
	----------
	start : Signal
		An active high strobe that indicates when the stream should be started.

	done: Signal
		An active high strobe that is generated when the transmission is completed.

	data: Array
		The data that is to be sent out.

	stream: T
		The stream interface being used to send the data.

	max_len: Signal | Int
		The max length to be sent. Only settable if `max_len_width` is set, Otherwise is read-only.
	'''

	def __init__(
		self, data_length: int, domain: str = 'sync', data_width: int = 8, stream_type: type[T] = StreamInterface,
		max_length_width: int | None = None
	) -> None:
		self._domain           = domain
		self._len              = data_length
		self._width            = data_width
		self._max_length_width = max_length_width

		self.start     = Signal()
		self.done      = Signal()

		self.data   = Array(Signal(self._width, name = f'datum_{i}') for i in range(self._len))
		self.stream = stream_type(data_width = self._width)

		if max_length_width:
			self.max_length = Signal(max_length_width)
		else:
			self.max_length = self._len

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		stream_pos = Signal(range(self._len))

		on_first = stream_pos == 0
		on_last  = (stream_pos == self._len - 1) | (stream_pos == self.max_length - 1)

		m.d.comb += [
			self.stream.first.eq(on_first & self.stream.valid),
			self.stream.last.eq(on_last & self.stream.valid),
		]

		with m.FSM(domain = self._domain) as fsm:
			m.d.comb += [ self.stream.valid.eq(fsm.ongoing('STREAMING')), ]

			with m.State('IDLE'):
				m.d.sync += [ stream_pos.eq(0), ]

				with m.If(self.start & (self.max_length > 1)):
					m.next = 'STREAMING'

			with m.State('STREAMING'):
				m.d.comb += [ self.stream.data.eq(self.data[stream_pos]), ]

				with m.If(self.stream.ready):
					should_continue = (
						((stream_pos + 1) < self.max_length) &
						((stream_pos + 1) < self._len)
					)

					with m.If(should_continue):
						m.d.sync += [ stream_pos.inc(), ]
					with m.Else():
						m.next = 'DONE'

			with m.State('DONE'):
				m.d.comb += [ self.done.eq(1), ]
				m.next = 'IDLE'

		if self._domain != 'sync':
			m = DomainRenamer(sync = self._domain)(m)

		return m
