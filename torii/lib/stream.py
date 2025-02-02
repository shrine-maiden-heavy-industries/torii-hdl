# SPDX-License-Identifier: BSD-2-Clause
from __future__      import annotations

from collections.abc import Iterable
from warnings        import warn

from ..hdl.ast       import Signal
from ..hdl.rec       import Record


__all__ = (
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

		rhs = ('valid', 'first', 'last', 'data', )
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
