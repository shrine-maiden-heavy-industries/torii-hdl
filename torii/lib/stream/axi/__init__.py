# SPDX-License-Identifier: BSD-2-Clause

'''
The :py:mod:`torii.lib.streams.axi` module contains the `AMBA® AXI5-Stream <https://developer.arm.com/documentation/ihi0051b/latest>`_
interface and associated machinery.

Important
---------
The :py:class:`.AXIStreamInterface` and it's related tooling is not directly compatible with the simple Torii
:py:class:`StreamInterface <torii.lib.stream.simple.StreamInterface>`.

''' # noqa: E501

from __future__  import annotations

from ....hdl.ast import Signal
from ....hdl.rec import Record

__all__ = (
	'AXIStreamInterface',
)

class AXIStreamInterface(Record):
	'''
	An AXI5-Stream interface in accordance to `IHI0051B <https://developer.arm.com/documentation/ihi0051b/latest>`_,
	The AMBA® AXI-Stream Protocol Specification.

	Parameters
	----------
	data_width : int
		The width of the stream data in bits.
		(default: 8)

		Note
		----
		This is recommended to be either ``8``, ``16``, ``32``, ``64``, ``128``, ``256``, ``512``,
		or ``1024`` bits.

	framing : bool
		Enable the ``tstrb``, ``tkeep``, and ``tlast`` stream framing signals.
		(default: False)

	wakeup : bool
		Enable the ``twakeup`` signal.
		(default: False)

	id_width : int
		Width of the ``tid`` signal in bits.
		(default: 0)

		Note
		----
		This value should be less than or equal to 8 at most.

	dest_width : int
		Width of the ``tdest`` signal in bits.
		(default: 0)

		Note
		----
		This value should be less than or equal to 8 at most.

	user_width : int
		Width of the ``tuser`` signal in bits.
		(default: 0)

		Note
		----
		It is recommended that ``user_width`` be an integer multiple of ``data_width // 8``.

	name : str | None
		The name of this record.

		If ``None``, it will use the name of the variable this is assigned to.

		(default: None)

	Attributes
	----------
	tvalid : Signal, trans
		Indication that the transmitter is driving a valid transfer.

		Transfers only take place when both ``tvalid`` and ``tready`` are asserted.

	tready : Signal, recv
		Indication that the receiver can accept the data.

	tdata : Signal(data_width), trans
		The data in the stream to be transmitted.

	tstrb : Signal(data_width // 8) | None, trans
		The byte qualifier for the ``tdata`` payload being transmitted indicating that the byte
		at that position is either a data byte or a position byte, if applicable.

		This signal is only present if ``framing`` is ``True``.

	tkeep : Signal(data_width // 8) | None, trans
		The byte qualifier for the ``tdata`` payload being transmitted indicating if that byte
		should be counted as part of the payload data, if applicable.

		This signal is only present if ``framing`` is ``True``.

	tlast :  Signal | None, trans
		Packet boundary indicator, if applicable.

		This signal is only present if ``framing`` is ``True``.

	tid : Signal(id_width) | None, trans
		The source data stream identifier, if applicable,

		This signal is only present if ``id_width`` is > ``0``.

	tdest : Signal(dest_width) | None, trans
		The stream routing information, if applicable.

		This signal is only present if ``dest_width`` is > ``0``.

	tuser : Signal(user_width) | None, trans
		User-defined sideband information that is transmitted along with ``tdata``.

		This signal is only present if ``user_width`` is > ``0``.

	twakeup : Signal | None, trans
		Indicates intention to transmit over the stream to the receiver.

		This signal is only present if ``wakeup`` is ``True``.
	'''

	tvalid: Signal
	tready: Signal
	tdata: Signal
	tstrb: Signal | None
	tkeep: Signal | None
	tlast: Signal | None
	tid: Signal | None
	tdest: Signal | None
	tuser: Signal | None
	twakeup: Signal | None

	def __init__(
		self, data_width: int = 8, *,
		framing: bool = False, wakeup: bool = False, id_width: int = 0, dest_width: int = 0, user_width: int = 0,
		name: str | None = None
	) -> None:

		self.data_width = data_width
		self.id_width   = id_width
		self.dest_width = dest_width
		self.user_width = user_width

		self.framing = framing
		self.wakeup  = wakeup

		layout: list[tuple[str, int]] = [
			('tvalid',               1),
			('tready',               1),
			('tdata',  self.data_width),
		]

		if self.id_width > 0:
			layout.append(('tid', self.id_width))

		if self.dest_width > 0:
			layout.append(('tdest', self.dest_width))

		if self.user_width > 0:
			layout.append(('tuser', self.user_width))

		if self.framing:
			layout += [
				('tstrb', self.data_width // 8),
				('tkeep', self.data_width // 8),
				('tlast',                    1),
			]

		if self.wakeup:
			layout.append(('twakeup', 1))

		super().__init__(layout, name = name, src_loc_at = 1)

	def _get_enabled(self, stream: AXIStreamInterface) -> list[str]:
		extra_outgoing: list[str] = []

		if self.id_width > 0 and stream.id_width > 0:
			extra_outgoing.append('tid')

		if self.dest_width > 0 and stream.dest_width > 0:
			extra_outgoing.append('tdest')

		if self.user_width > 0 and stream.user_width > 0:
			extra_outgoing.append('tuser')

		if self.framing and stream.framing:
			extra_outgoing += [
				'tstrb', 'tkeep', 'tlast',
			]

		if self.wakeup and stream.wakeup:
			extra_outgoing.append('twakeup')

		return extra_outgoing

	def attach(self, stream: AXIStreamInterface):
		'''
		Attach to the target stream.

		This establishes a connection to where we are the transmitting stream, and ``stream``
		is the receiving stream.

		.. code-block::

			self.tdata  -> stream.tdata
			self.tvalid -> stream.tvalid
			self.tready <- stream.tready

		The ``tid``, ``tdest``, and ``tuser`` signals are only connected if this stream and the target
		stream have ``id_width > 0``, ``dest_width > 0`` and ``user_width > 0`` respectively.

		.. code-block::

			self.tid -> stream.tid
			self.tdest -> stream.tdest
			self.tuser -> stream.tuser

		The ``tstrb``, ``tkeep``, and ``tlast`` signals are only connected if this stream and the target
		stream have the ``framing`` property set to ``True``.

		.. code-block::

			self.tstrb -> stream.tstrb
			self.tkeep -> stream.tkeep
			self.tlast -> stream.tlast

		Likewise, the ``twakeup`` signal is only connected if each stream has ``wakeup`` set to ``True``.

		.. code-block::

			self.twakeup -> stream.twakeup

		Parameters
		----------
		stream : torii.lib.stream.axi.AXIStreamInterface
			The stream we are attaching to.

		'''

		rhs = ('tvalid', 'tdata', *self._get_enabled(stream), )
		lhs = ('tready', )

		return [
			# Connect outgoing (from transmitter)
			*[ stream[field].eq(self[field]) for field in rhs ],
			# Connect incoming (from receiver)
			*[ self[field].eq(stream[field]) for field in lhs ],
		]

	def tap(self, stream: AXIStreamInterface):
		'''
		Attach a :py:class:`AXIStreamInterface` to this stream as a unidirectional tap.

		This joins all signals from this stream to ``stream`` as outgoing signals.

		.. code-block::

			self.tdata  -> stream.tdata
			self.tvalid -> stream.tvalid
			self.tready -> stream.tready

		'''

		signals = ('tready', 'tvalid', 'tdata', *self._get_enabled(stream), )

		return [ stream[sig].eq(self[sig]) for sig in signals ]
