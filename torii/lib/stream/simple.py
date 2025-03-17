# SPDX-License-Identifier: BSD-2-Clause

'''
The :py:mod:`torii.lib.streams.simple` module provides a simple and extensible unidirectional stream
interface :py:class:`.StreamInterface` as well as an :py:class:`Arbiter <.StreamArbiter>` to join multiple
streams into a single output stream.

'''

from __future__      import annotations

from collections.abc import Iterable
from typing          import Generic, TypeVar
from warnings        import warn

from ...hdl.ast      import Signal
from ...hdl.dsl      import Module
from ...hdl.ir       import Elaboratable
from ...hdl.rec      import Record
from ...hdl.xfrm     import DomainRenamer

__all__ = (
	'StreamArbiter',
	'StreamInterface',
)

class StreamInterface(Record):
	'''
	A simple interface representing a unidirectional stream.

	Parameters
	----------
	data_width : int
		The width of the stream data in bits.
		(default: 8)

	valid_width : int | None
		The width of the valid field. If ``None`` it will default to ``data_width // 8``.
		(default: 1)

	name : str | None
		The name of this stream.
		(default: None)

	extra : Iterable[tuple[str, int]]
		Any extra or ancillary fields to graft on to the stream.
		(default: [])

	Attributes
	----------
	data : Signal(data_width), send
		The data in the stream to be transmitted.

	valid : Signal(valid_width), send
		This can be two things, by default, when ``valid_width`` is ``data_width // 8``, it represents
		a set of bit flags for each byte in ``data`` determining if that byte of ``data`` is valid.

		For example, with ``data_width`` of ``16``, ``valid_width`` will be ``2``, where ``valid[0]`` is
		the valid flag for ``data[0:8]`` and ``valid[1]`` is the valid flag for ``data[8:16]``.

		When set to ``1`` it can simply mean that the whole of ``data`` is valid for this transaction. It
		can be as granular or corse as you wish, as long as both sides of the stream agree.

	first : Signal, send
		Indicates that the data is the first of the current packet.

	last : Signal, send
		Indicates that the data is the last of the current packet.

	ready : Signal, recv
		Indicates that the receiver will accept the data at the next active
		clock edge.

	payload : Signal(data_width), send (alias)
		This is a dynamic alias to the ``data`` member of the record.

	'''

	valid: Signal
	ready: Signal
	first: Signal
	last: Signal
	data: Signal

	def __init__(
		self, *,
		data_width: int = 8, valid_width: int | None = 1, name: str | None = None, extra: Iterable[tuple[str, int]] = []
	) -> None:

		self._extra_fields = extra

		if valid_width is None:
			valid_width = data_width // 8

		super().__init__([
			('data',  data_width),
			('valid', valid_width),
			('first', 1),
			('last',  1),
			('ready', 1),
			*extra
		], name = name, src_loc_at = 1)

	def connect(self, stream: StreamInterface, omit: set = set()):
		'''
		Connect to the target stream.

		This method is an alias for :py:meth:`StreamInterface.attach`.

		Parameters
		----------
		stream : torii.lib.stream.StreamInterface
			The stream we are attaching to.

		omit : set[str]
			A set of additional stream fields to exclude from the tap connection.
			(default: {})
		'''

		warn(
			'`StreamInterface.connect` has been deprecated, please use `StreamInterface.attach` instead.',
			DeprecationWarning,
			stacklevel = 2
		)

		return self.attach(stream, omit)

	def attach(self, stream: StreamInterface, omit: set = set()):
		'''
		Attach to a target stream.

		This method connects our ``valid``, ``first``, ``last``, and ``data`` fields to
		the downstream facing ``stream``, and their ``ready`` field to ours.

		This establishes a connection to where we are the originating stream, and ``stream``
		is the receiving stream.

		.. code-block::

			self.data  -> stream.data
			self.valid -> stream.valid
			self.first -> stream.first
			self.last  -> stream.last
			self.ready <- stream.ready

		Parameters
		----------
		stream : torii.lib.stream.StreamInterface
			The stream we are attaching to.

		omit : set[str]
			A set of additional stream fields to exclude from the tap connection.
			(default: {})
		'''

		rhs = ('valid', 'first', 'last', 'data', *self._extra_fields)
		lhs = ('ready', )
		att = [
			# Connect outgoing
			*[ stream[field].eq(self[field]) for field in rhs if field not in omit ],
			# Connect incoming
			*[ self[field].eq(stream[field]) for field in lhs if field not in omit ],
		]

		return att

	def stream_eq(self, stream: StreamInterface, omit: set = set()):
		'''
		Receive from target stream.

		This method connects the ``valid``, ``first``, ``last``, and ``data`` from ``stream`` to ours,
		and our ``ready`` field to theirs.

		This establishes a connection to where ``stream`` is the originating stream, and we are the receiving
		stream.

		.. code-block::

			self.data  <- stream.data
			self.valid <- stream.valid
			self.first <- stream.first
			self.last  <- stream.last
			self.ready -> stream.ready

		This function is effectively the inverse of :py:meth:`attach`, in fact, it's implementation
		is just:

		.. code-block:: python

			stream.attach(self, ...)

		It is provided as a more logical way to connect streams.

		Parameters
		----------
		stream : torii.lib.stream.StreamInterface
			The stream to attach to this stream.

		omit : set[str]
			A set of additional stream fields to exclude from the tap connection.
			(default: {})
		'''
		return stream.attach(self, omit = omit)

	def tap(self, stream: StreamInterface, *, tap_ready: bool = False, omit: set = set()):
		'''
		Attach a StreamInterface in read-only unidirectional tap mode.

		This joints all signals from ``stream`` to their matching signals in this stream.

		.. code-block::

			self.data  -> stream.data
			self.valid -> stream.valid
			self.first -> stream.first
			self.last  -> stream.last
			self.ready -> stream.ready

		Parameters
		----------
		stream : torii.lib.stream.StreamInterface
			The stream to use as the interface to this tap.

		tap_ready : bool
			By default the ``ready`` signal is excluded from the tap, passing ``True`` here will also
			connect that signal.
			(default: False)

		omit : set[str]
			A set of additional stream fields to exclude from the tap connection.
			(default: {})
		'''

		tap = self.stream_eq(stream, {'ready', *omit})

		# If we are also snooping on the `ready` signal then glue that on
		if tap_ready:
			tap.append(self.ready.eq(stream.ready))

		# Return the tap
		return tap

	def __getattr__(self, name: str):

		# Re-map the `payload` alias to `data`
		if name == 'payload':
			warn(
				'StreamInterface alias \'payload\' is deprecated, use \'data\' instead',
				DeprecationWarning,
				stacklevel = 2
			)
			name = 'data'

		return super().__getattr__(name)

T = TypeVar('T', bound = StreamInterface)
class StreamArbiter(Generic[T], Elaboratable):
	'''
	A simple multi-input-single-output stream arbiter.

	This uses a very simple priority scheduler and relies on the standard ``valid``/``ready`` handshake
	that occurs between streams to schedule which stream is connected to the output stream.

	Parameters
	----------
	domain : str
		The domain in which the arbiter should operate.
		(default: sync)

	stream_type : type
		The type of stream to create, must be either :py:class:`StreamInterface <torii.lib.stream.StreamInterface>`
		or a subtype there of.
		(default: torii.lib.stream.StreamInterface)

	Attributes
	----------
	out : stream_type, out
		The output stream.

	idle : Signal, out
		Indicates the arbiter is idle, this occurs when the input source stream is not active.

	'''

	def __init__(self, *, domain: str = 'sync', stream_type: type[T] = StreamInterface) -> None:
		self._domain = domain

		self._sources: list[T] = list()

		self.out  = stream_type()
		self.idle = Signal()

	def connect(self, stream: T, priority: int = -1) -> None:
		'''
		Connect an output stream to the arbiter.

		Parameters
		----------
		stream : torii.lib.stream.StreamInterface
			The stream to connect to the arbiter.

		priority : int
			The stream priority.
			(default: -1)
		'''
		if priority > 0:
			self._sources.append(stream)
		else:
			self._sources.insert(priority, stream)

	def elaborate(self, _) -> Module:
		m = Module()

		count = len(self._sources)
		index = Signal(range(count))

		with m.Switch(index):
			for idx, stream in enumerate(self._sources):
				with m.Case(idx):
					m.d.comb += [ self.out.stream_eq(stream), ]

		with m.If(~self.out.valid):
			m.d.comb += [ self.idle.eq(1), ]

			for idx in reversed(range(count)):
				with m.If(self._sources[idx].valid):
					m.d.comb += [ self.idle.eq(0), ]
					m.d.sync += [ index.eq(idx),   ]

		if self._domain != 'sync':
			m = DomainRenamer(sync = self._domain)(m)

		return m


class StreamMultiplexer(Generic[T], Elaboratable):
	'''
	Gateware that merges a collection of StreamInterfaces into a single interface.

	This variant performs no scheduling. Assumes that only one stream will be communicating at once.

	Attributes
	----------
	output: StreamInterface(), output stream
		Our output interface; has all of the active busses merged together.

	'''

	def __init__(self, stream_type: type[T] = StreamInterface) -> None:
		'''
		Parameters
		----------
		stream_type
			The type of stream we'll be multiplexing. Must be a subclass of StreamInterface.

		'''

		# Collection that stores each of the interfaces added to this bus.
		self._inputs: list[T] = []

		#
		# I/O port
		#
		self.output = stream_type()

	def add_input(self, input_interface: T) -> None:

		''' Adds a transmit interface to the multiplexer. '''
		self._inputs.append(input_interface)

	def elaborate(self, platform) -> Module:
		m = Module()

		#
		# Our basic functionality is simple: we'll build a priority encoder that
		# connects whichever interface has its .valid signal high.
		#

		conditional = m.If

		for interface in self._inputs:

			# If the given interface is asserted, drive our output with its signals.
			with conditional(interface.valid):
				m.d.comb += interface.attach(self.output)

			# After our first iteration, use Elif instead of If.
			conditional = m.Elif

		return m
