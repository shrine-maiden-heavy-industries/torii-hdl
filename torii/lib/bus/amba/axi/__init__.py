# SPDX-License-Identifier: BSD-2-Clause

'''

.. _AMBA5: https://developer.arm.com/Architectures/AMBA
.. _IHI0022: https://developer.arm.com/documentation/ihi0022/latest

ARM `AMBA5`_ Advanced eXtensible Interface (AXI)
------------------------------------------------

For detailed information see ARM technical document `IHI0022`_.

For AXI Streams see :py:mod:`torii.lib.stream.axi`

'''

from math         import ceil
from enum         import Enum, unique, auto
from typing       import TypeAlias, Literal

from .....hdl.rec import Record, Direction

__all__ = (
	'ChannelType',
	'InterfaceType',
	'BusType',
	'ReadChannel',
	'WriteChannel',
	'SnoopChannel',
	'Interface',
)

@unique
class ChannelType(Enum):
	READ   = auto()
	WRITE  = auto()
	SNOOP  = auto()

@unique
class InterfaceType(Enum):
	MANAGER     = auto()
	SUBORDINATE = auto()

@unique
class BusType(Enum):
	FULL   = auto()
	LITE   = auto()

BusWidth: TypeAlias = Literal[8, 16, 32, 64, 128, 256, 512, 1024]
BusSnoopWidth: TypeAlias = Literal[0, 4]
BusFeature: TypeAlias = Literal['atomic', 'qos', 'region', 'wakeup', 'burst']
BusFeatures: TypeAlias = set[BusFeature] | frozenset[BusFeature]

def _fanout_if_mgr(interface_type: InterfaceType) -> Direction:
	match interface_type:
		case InterfaceType.MANAGER:
			return Direction.FANOUT
		case InterfaceType.SUBORDINATE:
			return Direction.FANIN

def _fanin_if_mgr(interface_type: InterfaceType) -> Direction:
	match interface_type:
		case InterfaceType.MANAGER:
			return Direction.FANIN
		case InterfaceType.SUBORDINATE:
			return Direction.FANOUT

def _check_id_width(width: int) -> None:
	if width not in range(0, 33):
		raise ValueError(f'id_width must be between 0 and 32, not \'{width}\'.')

def _check_snoop_width(width: int, bus_type: BusType) -> None:
	if bus_type == BusType.LITE and width != 0:
		raise ValueError(f'snoop_width must be 0 for AXI-Lite busses not \'{width}\'.')
	elif width not in (0, 4):
		raise ValueError(f'snoop_width must be either 0 or 4, not \'{width}\'.')

def _check_loop_width(width: int, bus_type: BusType) -> None:
	if bus_type == BusType.LITE and width != 0:
		raise ValueError(f'loop_width must be 0 for AXI-Lite busses not \'{width}\'.')
	elif width not in range(0, 9):
		raise ValueError(f'loop_width must be between 0 and 8, not \'{width}\'.')

def _check_addr_width(width: int) -> None:
	if width not in range(1, 65):
		raise ValueError(f'addr_width must be between 1 and 64, not \'{width}\'.')

def _check_data_width(width: int, bus_type: BusType) -> None:
	if bus_type == BusType.LITE and width not in (32, 64):
		raise ValueError(f'data_width must be either 32 or 64, not \'{width}\'.')
	elif width not in (8, 16, 32, 64, 128, 256, 512, 1024):
		raise ValueError(f'data_width must be one of: 8, 16, 32, 64, 128, 256, 512 or 1024, not \'{width}\'.')

def _check_widths(
	*, addr_width: int, data_width: int, id_width: int, snoop_width: int, loop_width: int, bus_type: BusType
) -> None:
	_check_addr_width(addr_width)
	_check_data_width(data_width, bus_type)
	_check_id_width(id_width)
	_check_snoop_width(snoop_width, bus_type)
	_check_loop_width(loop_width, bus_type)


def _check_features(features, bus_type: BusType) -> None:
	unknown = set(features) - { 'atomic', 'qos', 'region', 'wakeup', 'burst' }

	if unknown:
		raise ValueError(f'Optional feature(s) {", ".join(map(repr, unknown))} are not supported')

	if bus_type == BusType.LITE and 'atomic' in features:
		raise ValueError('AXI-Lite busses don\'t support the \'atomic\' feature.')

class WriteChannel(Record):
	'''

	On an AXI bus, write channels are used to transfer requests, data, and responses for write transactions
	as well as other data-less transactions.

	It is made up of 3 parts:

	* Write Request Channel
	* Write Data Channel
	* Write Response Channel

	Parameters
	----------
	addr_width : int
		The width of the address on the AXI bus (must be between 1 and 64).

	data_width : Literal[8, 16, 32, 64, 128, 256, 512, 1024]
		The width of the data payload on the AXI bus.

		Note
		----
		On AXI-Lite busses, this can only be either 32 or 64

	bus_type : BusType
		The type of bus this channel is constructed for, either Full or Lite.

	interface_type : InterfaceType
		The type of the interface this channel is constructed for, either Manager or Subordinate.

	id_width : int
		The width of the ID field of this channel.
		(default: 0)

	snoop_width : int
		The width of the snoop field of this channel.
		(default: 0)

	loop_width : int
		The width of the loop field of this channel.
		(default: 0)

	features : set[BusFeature]
		The features on the bus this channel is being constructed for.
		(default: frozenset())

	Attributes
	----------
	addr_width : int
		The width of addresses on the AXI bus.

	data_width : int
		The width of the data payload on the AXI bus.

	id_width : int
		The width of the ID signals on the AXI bus.

	user_req_width : int
	user_rsp_width : int
	user_dat_width : int
	snoop_width : int
	loop_width : int
	secsid_width : int
	sid_width : int
	ssid_width : int
	subsysid_width : int
	mpam_width : int
	awcmo_width : int
	mecid_width : int
	resp_width : int

	poison_width : int
		The poison indication width, defined as ``ceil(data_width / 64)``.

	strb_width : int
		The data strobe width, defined as ``data_width // 8``.

	tag_width : int
		The transaction tag width, defined as ``ceil(data_width / 128)``

	bus_type : BusType
		The type of AXI bus this is, either Full or Lite

	interface_type : InterfaceType
		The type of interface this channel is being added to, either Manager or Subordinate.

	features : frozenset[BusFeature]
		The features enabled on this AXI bus.
		(defualt: frozenset())

	awvalid : Signal(1)


	awready : Signal(1)


	awid : Signal(id_width) | None


	awaddr : Signal(addr_width)


	awregion : Signal(4)


	awlen : Signal(8)


	awsize : Signal(3)


	awburst : Signal(2)


	awlock : Signal(1)


	awcache : Signal(4)


	awprot : Signal(3)


	awnse : Signal(1)


	awqos : Signal(4)


	awuser : Signal(user_req_width)


	awdomain : Signal(2)


	awsnoop : Signal(snoop_width)


	awstashnid : Signal(11)


	awstashiden : Signal(1)


	awstashlpid : Signal(5)


	awstashlpiden : Signal(1)


	awtrace : Signal(1)


	awloop : Signal(loop_width)


	awmmuvalid : Signal(1)


	awmmusecsi : Signal(secsid_width)


	awmmusid : Signal(sid_width)


	awmmussidv : Signal(1)


	awmmussid : Signal(ssid_width)


	awmmuatst : Signal(1)


	awmmuflow : Signal(2)


	awpbha : Signal(4)


	awnsaid : Signal(4)


	awsubsysid : Signal(subsysid_width)


	awatop : Signal(6)


	awmpam : Signal(mpam_width)


	awidunq : Signal(1)


	awcmo : Signal(awcmo_width)


	awtagop : Signal(2)


	awmeccid : Signal(mecid_width)


	wvalid : Signal(1)


	wready : Signal(1)


	wdata : Signal(data_width)


	wstrb : Signal(strb_width)


	wtag : Signal(tag_width * 4)


	wtagupdate : Signal(tag_width)


	wlast : Signal(1)


	wuser : Signal(user_dat_width)


	wpoison : Signal(poison_width)


	wtrace : Signal(1)


	bvalid : Signal(1)
		Response valid indicator signal originating from the subordinate interface.

	bready : Signal(1)
		Response ready indicator signal originating from the manager interface.

	bid : Signal(id_width)
		Response transaction ID originating from the subordinate interface.

	bidunq : Signal(1)
		Response unique ID indicator originating from the subordinate interface.

	bresp : Signal(resp_width)
		Response signal originating from the subordinate interface.

	bcomp : Signal(1)
		Response completion signal originating from the subordinate interface.

	bpersist : Signal(1)
		Response persist response signal originating from the subordinate interface.

	btagmatch : Signal(2)
		Response memory tag match signal originating from the subordinate interface.

	buser : Signal(user_rsp_width)
		Response user-defined extension originating from the subordinate interface.

	btrace : Signal(1)
		Response trace signal originating from the subordinate interface.

	bloop : Signal(loop_width)
		Response loopback signals originating from the subordinate interface.

	bbusy : Signal(2)
		Response busy indicator signal originating from the subordinate interface.

	'''

	def __init__(
		self, addr_width: int, data_width: BusWidth, bus_type: BusType, interface_type: InterfaceType, *,
		id_width: int = 0, snoop_width: int = 0, loop_width: int = 0, features: BusFeatures = frozenset()
	):
		_check_widths(
			addr_width = addr_width, data_width = data_width, id_width = id_width,
			snoop_width = snoop_width, loop_width = loop_width,
			bus_type = bus_type
		)
		_check_features(features, bus_type)

		self.addr_width     = addr_width
		self.data_width     = data_width
		self.id_width       = id_width
		self.user_req_width = 0
		self.user_rsp_width = 0
		self.user_dat_width = 0
		self.snoop_width    = snoop_width
		self.loop_width     = loop_width
		self.secsid_width   = 0
		self.sid_width      = 0
		self.ssid_width     = 0
		self.subsysid_width = 0
		self.mpam_width     = 0
		self.awcmo_width    = 0
		self.mecid_width    = 0
		self.resp_width     = 0
		self.poison_width   = ceil(self.data_width / 64)
		self.strb_width     = self.data_width // 8
		self.tag_width      = ceil(self.data_width / 128)
		self.bus_type       = bus_type
		self.interface_type = interface_type
		self.features       = set(features)

		super().__init__(self._assemble_channel())

	def _assemble_channel(self) -> list[tuple[str, int, Direction]]:
		MGR_FANIN  = _fanin_if_mgr(self.interface_type)
		MGR_FANOUT = _fanout_if_mgr(self.interface_type)

		# Common to Lite and Full
		_layout: list[tuple[str, int, Direction]] = [
			# Request
			('awvalid',                      1, MGR_FANOUT), # Valid indicator
			('awready',                      1, MGR_FANIN ), # Ready indicator
			('awid',             self.id_width, MGR_FANOUT), # Transaction identifier for the write channels
			('awaddr',         self.addr_width, MGR_FANOUT), # Transaction address
			('awregion',                     4, MGR_FANOUT), # Region identifier
			('awlen',                        8, MGR_FANOUT), # Transaction length
			('awsize',                       3, MGR_FANOUT), # Transaction size
			('awburst',                      2, MGR_FANOUT), # Burst attribute
			('awlock',                       1, MGR_FANOUT), # Exclusive access indicator
			('awcache',                      4, MGR_FANOUT), # Memory attributes
			('awprot',                       3, MGR_FANOUT), # Access attributes
			('awnse',                        1, MGR_FANOUT), # Non-secure extension bit for RME
			('awqos',                        4, MGR_FANOUT), # QoS identifier
			('awuser',     self.user_req_width, MGR_FANOUT), # User-defined extension to a request
			('awdomain',                     2, MGR_FANOUT), # Shareability domain of a request
			('awsnoop',       self.snoop_width, MGR_FANOUT), # Write request opcode
			('awstashnid',                  11, MGR_FANOUT), # Stash Node ID
			('awstashiden',                  1, MGR_FANOUT), # Stash Node ID enable
			('awstashlpid',                  5, MGR_FANOUT), # Stash Logical Processor ID
			('awstashlpiden',                1, MGR_FANOUT), # Stash Logical Processor ID enable
			('awtrace',                      1, MGR_FANOUT), # Trace signal
			('awloop',         self.loop_width, MGR_FANOUT), # Loopback signals on the write channels
			('awmmuvalid',                   1, MGR_FANOUT), # MMU signal qualifier
			('awmmusecsi',   self.secsid_width, MGR_FANOUT), # Secure Stream ID
			('awmmusid',        self.sid_width, MGR_FANOUT), # StreamID
			('awmmussidv',                   1, MGR_FANOUT), # SubstreamID valid
			('awmmussid',      self.ssid_width, MGR_FANOUT), # SubstreamID
			('awmmuatst',                    1, MGR_FANOUT), # Address translated indicator
			('awmmuflow',                    2, MGR_FANOUT), # SMMU flow type
			('awpbha',                       4, MGR_FANOUT), # Page-based Hardware Attributes
			('awnsaid',                      4, MGR_FANOUT), # Non-secure Access ID
			('awsubsysid', self.subsysid_width, MGR_FANOUT), # Subsystem ID
			('awatop',                       6, MGR_FANOUT), # Atomic transaction opcode
			('awmpam',         self.mpam_width, MGR_FANOUT), # MPAM information with a request
			('awidunq',                      1, MGR_FANOUT), # Unique ID indicator
			('awcmo',         self.awcmo_width, MGR_FANOUT), # CMO type
			('awtagop',                      2, MGR_FANOUT), # Memory Tag operation for write requests
			('awmeccid',      self.mecid_width, MGR_FANOUT), # Memory Encryption Context identifier
			# Data
			('wvalid',                       1, MGR_FANOUT), # Valid indicator
			('wready',                       1, MGR_FANIN ), # Ready indicator
			('wdata',          self.data_width, MGR_FANOUT), # Write data
			('wstrb',          self.strb_width, MGR_FANOUT), # Write data strobes
			('wtag',        self.tag_width * 4, MGR_FANOUT), # Memory Tag
			('wtagupdate',      self.tag_width, MGR_FANOUT), # Memory Tag update
			('wlast',                        1, MGR_FANOUT), # Last write data
			('wuser',      self.user_dat_width, MGR_FANOUT), # User-defined extension to write data
			('wpoison',      self.poison_width, MGR_FANOUT), # Poison indicator
			('wtrace',                       1, MGR_FANOUT), # Trace signal
			# Response
			('bvalid',                       1, MGR_FANIN ), # Valid indicator
			('bready',                       1, MGR_FANOUT), # Ready indicator
			('bid',              self.id_width, MGR_FANIN ), # Transaction identifier for the write channels
			('bidunq',                       1, MGR_FANIN ), # Unique ID indicator
			('bresp',          self.resp_width, MGR_FANIN ), # Write response
			('bcomp',                        1, MGR_FANIN ), # Completion response indicator
			('bpersist',                     1, MGR_FANIN ), # Persist response
			('btagmatch',                    2, MGR_FANIN ), # Memory Tag Match response
			('buser',      self.user_rsp_width, MGR_FANIN ), # User-defined extension to a write response
			('btrace',                       1, MGR_FANIN ), # Trace signal
			('bloop',          self.loop_width, MGR_FANIN ), # Loopback signals on the write channels
			('bbusy',                        2, MGR_FANIN ), # Busy indicator
		]

		# ID - Transaction identifier for the write channels
		if self.id_width < 0:
			_layout += [
				# Request

				# Response

			]

		if self.bus_type == BusType.FULL:
			_layout += [
				# Request

				# Data

				# Response

			]

		if 'atomic' in self.features:
			_layout += [
				# Request

				# Data

				# Response

			]

		if 'qos' in self.features:
			_layout += [
				# Request

				# Data

				# Response
			]

		if 'region' in self.features:
			_layout += [
				# Request

				# Data

				# Response

			]

		if 'wakeup' in self.features:
			_layout += [
				# Request

				# Data

				# Response

			]

		if 'burst' in self.features:
			_layout += [
				# Request

				# Data

				# Response

			]

		return _layout

class ReadChannel(Record):
	'''


	Parameters
	----------
	addr_width : int
		The width of the address on the AXI bus (must be between 1 and 64).

	data_width : Literal[8, 16, 32, 64, 128, 256, 512, 1024]
		The width of the data payload on the AXI bus.

		Note
		----
		On AXI-Lite busses, this can only be either 32 or 64

	bus_type : BusType
		The type of bus this channel is constructed for, either Full or Lite.

	interface_type : InterfaceType
		The type of the interface this channel is constructed for, either Manager or Subordinate.

	id_width : int
		The width of the ID field of this channel.
		(default: 0)

	snoop_width : int
		The width of the snoop field of this channel.
		(default: 0)

	loop_width : int
		The width of the loop field of this channel.
		(default: 0)

	features : set[BusFeature]
		The features on the bus this channel is being constructed for.
		(default: frozenset())

	Attributes
	----------
	addr_width :


	data_width :


	id_width :


	user_rsp_width :


	user_req_width :


	user_dat_width :


	snoop_width :


	loop_width :


	secsid_width :


	sid_width :


	ssid_width :


	subsysid_width :


	mpam_width :


	mecid_width :


	resp_width :


	chunkn_width :


	chunks_width :


	poison_width :


	strb_width :


	tag_width :


	bus_type :


	interface_type :


	features  : frozenset[BusFeature]
		The features enabled on this AXI bus.
		(defualt: frozenset())

	arvalid : Signal()


	arready : Signal()


	arid : Signal()


	araddr : Signal()


	arregion : Signal()


	arlen : Signal()


	arsize : Signal()


	arburst : Signal()


	arlock : Signal()


	arcache : Signal()


	arprot : Signal()


	arnse : Signal()


	arqos : Signal()


	aruser : Signal()


	ardomain : Signal()


	arsnoop : Signal()


	artrace : Signal()


	arloop : Signal()


	armmuvalid : Signal()


	armmusecsid : Signal()


	armmusid : Signal()


	armmussidv : Signal()


	armmussid : Signal()


	armmuatst : Signal()


	armmuflow : Signal()


	arpbha : Signal()


	arnsaid : Signal()


	arsubsysid : Signal()


	armpam : Signal()


	archunken : Signal()


	aridunq : Signal()


	artagop : Signal()


	armecid : Signal()


	rvalid : Signal()


	rready : Signal()


	rid : Signal()


	ridun1 : Signal()


	rdata : Signal()


	rtag : Signal()


	rresp : Signal()


	rlast : Signal()


	ruser : Signal()


	rpoison : Signal()


	rtrace : Signal()


	rloop : Signal()


	rchunkv : Signal()


	rchunknum : Signal()


	rchunkstrb : Signal()


	rbusy : Signal()



	'''

	def __init__(
		self, addr_width: int, data_width: BusWidth, bus_type: BusType, interface_type: InterfaceType, *,
		id_width: int = 0, snoop_width: int = 0, loop_width: int = 0, features: BusFeatures = frozenset()
	):
		_check_widths(
			addr_width = addr_width, data_width = data_width, id_width = id_width,
			snoop_width = snoop_width, loop_width = loop_width,
			bus_type = bus_type
		)
		_check_features(features, bus_type)

		self.addr_width     = addr_width
		self.data_width     = data_width
		self.id_width       = id_width
		self.user_rsp_width = 0
		self.user_req_width = 0
		self.user_dat_width = 0
		self.snoop_width    = snoop_width
		self.loop_width     = loop_width
		self.secsid_width   = 0
		self.sid_width      = 0
		self.ssid_width     = 0
		self.subsysid_width = 0
		self.mpam_width     = 0
		self.mecid_width    = 0
		self.resp_width     = 0
		self.chunkn_width   = 0
		self.chunks_width   = 0
		self.poison_width   = ceil(self.data_width / 64)
		self.strb_width     = self.data_width // 8
		self.tag_width      = ceil(self.data_width / 128)
		self.bus_type       = bus_type
		self.interface_type = interface_type
		self.features       = set(features)

		super().__init__(self._assemble_channel())

	def _assemble_channel(self) -> list[tuple[str, int, Direction]]:
		MGR_FANIN  = _fanin_if_mgr(self.interface_type)
		MGR_FANOUT = _fanout_if_mgr(self.interface_type)

		# Common to Lite and Full
		_layout: list[tuple[str, int, Direction]] = [
			# Request
			('arvalid',                      1, MGR_FANOUT), # Valid indicator
			('arready',                      1, MGR_FANIN ), # Ready indicator
			('arid',             self.id_width, MGR_FANOUT), # Transaction identifier for the read channels
			('araddr',         self.addr_width, MGR_FANOUT), # Transaction address
			('arregion',                     4, MGR_FANOUT), # Region identifier
			('arlen',                        8, MGR_FANOUT), # Transaction length
			('arsize',                       3, MGR_FANOUT), # Transaction size
			('arburst',                      2, MGR_FANOUT), # Burst attribute
			('arlock',                       1, MGR_FANOUT), # Exclusive access indicator
			('arcache',                      4, MGR_FANOUT), # Memory attributes
			('arprot',                       3, MGR_FANOUT), # Access attributes
			('arnse',                        1, MGR_FANOUT), # Non-secure extension bit for RME
			('arqos',                        1, MGR_FANOUT), # QoS identifier
			('aruser',     self.user_req_width, MGR_FANOUT), # User-defined extension to a request
			('ardomain',                     2, MGR_FANOUT), # Shareability domain of a request
			('arsnoop',       self.snoop_width, MGR_FANOUT), # Read request opcode
			('artrace',                      1, MGR_FANOUT), # Trace signal
			('arloop',         self.loop_width, MGR_FANOUT), # Loopback signals on the read channels
			('armmuvalid',                   1, MGR_FANOUT), # MMU signal qualifier
			('armmusecsid',  self.secsid_width, MGR_FANOUT), # Secure Stream ID
			('armmusid',        self.sid_width, MGR_FANOUT), # StreamID
			('armmussidv',                   1, MGR_FANOUT), # SubstreamID valid
			('armmussid',      self.ssid_width, MGR_FANOUT), # SubstreamID
			('armmuatst',                    1, MGR_FANOUT), # Address translated indicator
			('armmuflow',                    2, MGR_FANOUT), # SMMU flow type
			('arpbha',                       4, MGR_FANOUT), # Page-based Hardware Attributes
			('arnsaid',                      4, MGR_FANOUT), # Non-secure Access ID
			('arsubsysid', self.subsysid_width, MGR_FANOUT), # Subsystem ID
			('armpam',         self.mpam_width, MGR_FANOUT), # MPAM information with a request
			('archunken',                    1, MGR_FANOUT), # Read data chunking enable
			('aridunq',                      1, MGR_FANOUT), # Unique ID indicator
			('artagop',                      2, MGR_FANOUT), # Memory Tag operation for read requests
			('armecid',       self.mecid_width, MGR_FANOUT), # Memory Encryption Context identifier
			# Data
			('rvalid',                       1, MGR_FANIN ), # Valid indicator
			('rready',                       1, MGR_FANOUT), # Ready indicator
			('rid',              self.id_width, MGR_FANIN ), # Transaction identifier for the read channels
			('ridun1',                       1, MGR_FANIN ), # Unique ID indicator
			('rdata',          self.data_width, MGR_FANIN ), # Read data
			('rtag',        self.tag_width * 4, MGR_FANIN ), # Memory Tag
			('rresp',          self.resp_width, MGR_FANIN ), # Read response
			('rlast',                        1, MGR_FANIN, ), # Last read data
			('ruser',   self.user_dat_width + self.user_rsp_width, MGR_FANIN ), # User-defined extension to read data and response # noqa: E501
			('rpoison',      self.poison_width, MGR_FANIN ), # Poison indicator
			('rtrace',                       1, MGR_FANIN ), # Trace signal
			('rloop',          self.loop_width, MGR_FANIN ), # Loopback signals on the read channels
			('rchunkv',                      1, MGR_FANIN ), # Read data chunking valid
			('rchunknum',    self.chunkn_width, MGR_FANIN ), # Read data chunk number
			('rchunkstrb',   self.chunks_width, MGR_FANIN ), # Read data chunk strobe
			('rbusy',                        2, MGR_FANIN ), # Busy indicator
		]

		# ID - Transaction identifier for the write channels
		if self.id_width < 0:
			_layout += [
				# Request

				# Data

			]

		if self.bus_type == BusType.FULL:
			_layout += [
				# Request

				# Data

			]

		if 'atomic' in self.features:
			_layout += [
				# Request

				# Data

			]

		if 'qos' in self.features:
			_layout += [
				# Request

				# Data

			]

		if 'region' in self.features:
			_layout += [
				# Request

				# Data

			]

		if 'wakeup' in self.features:
			_layout += [
				# Request

				# Data

			]

		if 'burst' in self.features:
			_layout += [
				# Request

				# Data

			]

		return _layout

class SnoopChannel(Record):
	'''

	A channel on an AXI bus only used to transmit DVM messages.

	Parameters
	----------
	addr_width : int
		The width of the address on the AXI bus.

	bus_type : BusType
		The type of AXI bus this is (Full or Lite).

	interface_type : InterfaceType
		The side of the interface this channel is on.


	Attributes
	----------
	addr_width : int
		The width of the address on the AXI bus.

	bus_type : BusType
		The type of AXI bus this is (Full or Lite).

	interface_type : InterfaceType
		The side of the interface this channel is on.

	acvalid : Signal(1)
		Request valid indicator originating from the subordinate interface.

	acready : Signal(1)
		Request ready signal originating from the manager interface.

	acaddr : Signal(addr_width)
		Request DVM message payload originating from the subordinate interface.

	acvmidext : Signal(4)
		Request VMID extension for DVM messages originating from the subordinate interface.

	actrace : Signal(1)
		Request trace signal originating from the subordinate interface.

	crvalid : Signal(1)
		Response valid indicator originating from the manager interface.

	crready : Signal(1)
		Response ready indicator originating from the subordinate interface.

	crtrace : Signal(1)
		Response trace signal originating from the manager interface.


	'''

	def __init__(
		self, addr_width: int, bus_type: BusType, interface_type: InterfaceType,
	):
		_check_addr_width(addr_width)

		self.addr_width     = addr_width
		self.bus_type       = bus_type
		self.interface_type = interface_type

		super().__init__(self._assemble_channel())

	def _assemble_channel(self) -> list[tuple[str, int, Direction]]:
		MGR_FANIN  = _fanin_if_mgr(self.interface_type)
		MGR_FANOUT = _fanout_if_mgr(self.interface_type)

		_layout: list[tuple[str, int, Direction]] = [
			# Request
			('acvalid',                 1, MGR_FANIN ), # Valid indicator
			('acready',                 1, MGR_FANOUT), # Ready indicator
			('acaddr',    self.addr_width, MGR_FANIN ), # DVM message payload
			('acvmidext',               4, MGR_FANIN ), # VMID extension for DVM messages
			('actrace',                 1, MGR_FANIN ), # Trace signal
			# Response
			('crvalid',                 1, MGR_FANOUT), # Valid indicator
			('crready',                 1, MGR_FANIN ), # Ready indicator
			('crtrace',                 1, MGR_FANOUT), # Trace signal
		]

		return _layout

class Interface(Record):
	'''

	Parameters
	----------
	addr_width : int
		The width of the address on the AXI bus (must be between 1 and 64).

	data_width : Literal[8, 16, 32, 64, 128, 256, 512, 1024]
		The width of the data payload on the AXI bus.

		Note
		----
		On AXI-Lite busses, this can only be either 32 or 64

	bus_type : BusType
		The type of bus.

	interface_type : InterfaceType
		The type of the interface.

	id_width : int
		The width of the ID field of the channels in this interface.
		(default: 0)

	snoop_width : int
		The width of the snoop field of the channels in this interface.
		(default: 0)

	loop_width : int
		The width of the loop field of the channels in this interface.
		(default: 0)

	features : set[BusFeature]
		The features on this interface.
		(default: frozenset())

	'''

	def __init__(
		self, addr_width: int, data_width: BusWidth, bus_type: BusType, interface_type: InterfaceType, *,
		id_width: int = 0, snoop_width: int = 0, loop_width: int = 0, features: BusFeatures = frozenset()
	):
		_check_widths(
			addr_width = addr_width, data_width = data_width, id_width = id_width,
			snoop_width = snoop_width, loop_width = loop_width,
			bus_type = bus_type
		)
		_check_features(features, bus_type)

		self.addr_width     = addr_width
		self.data_width     = data_width
		self.id_width       = id_width
		self.bus_type       = bus_type
		self.interface_type = interface_type
		self.features       = set(features)

		self.write_channel  = WriteChannel(
			addr_width, data_width, bus_type, interface_type,
			id_width = id_width, snoop_width = snoop_width, loop_width = loop_width,
			features = features
		)
		self.read_channel  = ReadChannel(
			addr_width, data_width, bus_type, interface_type,
			id_width = id_width, snoop_width = snoop_width, loop_width = loop_width,
			features = features
		)
		self.snoop_channel  = SnoopChannel(
			addr_width, data_width, bus_type, interface_type,
			id_width = id_width, snoop_width = snoop_width, loop_width = loop_width,
			features = features
		)

		super().__init__(self._assemble_interface())

	def _assemble_interface(self) -> list[tuple[str, int, Direction]]:
		MGR_FANIN  = _fanin_if_mgr(self.interface_type)
		MGR_FANOUT = _fanout_if_mgr(self.interface_type)

		_layout: list[tuple[str, int, Direction]] = [
			('aclk',  1, Direction.NONE),
			('arstn', 1, Direction.NONE),
			*list(self.write_channel.layout),
			*list(self.read_channel.layout),
			*list(self.snoop_channel.layout),
			('syscoreq', 1, MGR_FANOUT),
			('syscoack', 1, MGR_FANIN ),
		]

		if 'qos' in self.features:
			_layout += [
				('vawqosaccept', 4, MGR_FANIN ),
				('varqosaccept', 4, MGR_FANIN ),
			]

		if 'wakeup' in self.features:
			_layout += [
				('awakeup',  1, MGR_FANOUT),
				('acwakeup', 1, MGR_FANIN ),
			]

		return _layout
