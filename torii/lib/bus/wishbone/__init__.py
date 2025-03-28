# SPDX-License-Identifier: BSD-2-Clause

from collections.abc import Iterable
from enum            import Enum
from typing          import Literal

from ....hdl.ast     import Cat, Signal
from ....hdl.dsl     import Module
from ....hdl.ir      import Elaboratable
from ....hdl.rec     import Direction, Record
from ....util.units  import log2_exact
from ...mem.map      import MemoryMap

__all__ = (
	'Arbiter',
	'BurstTypeExt',
	'CycleType',
	'Decoder',
	'Interface',
)

class CycleType(Enum):
	''' Wishbone Registered Feedback cycle type. '''
	CLASSIC      = 0b000
	CONST_BURST  = 0b001
	INCR_BURST   = 0b010
	END_OF_BURST = 0b111

class BurstTypeExt(Enum):
	''' Wishbone Registered Feedback burst type extension. '''
	LINEAR  = 0b00
	WRAP_4  = 0b01
	WRAP_8  = 0b10
	WRAP_16 = 0b11

def _check_interface(
	addr_width: int, data_width: int, granularity: int,
	features: Iterable[Literal['rty', 'err', 'stall', 'lock', 'cti', 'bte']]
) -> None:
	if not isinstance(addr_width, int) or addr_width < 0:
		raise ValueError(f'Address width must be a non-negative integer, not {addr_width!r}')
	if data_width not in (8, 16, 32, 64):
		raise ValueError(f'Data width must be one of 8, 16, 32, 64, not {data_width!r}')
	if granularity not in (8, 16, 32, 64):
		raise ValueError(f'Granularity must be one of 8, 16, 32, 64, not {granularity!r}')
	if granularity > data_width:
		raise ValueError(f'Granularity {granularity} may not be greater than data width {data_width}')
	unknown = set(features) - { 'rty', 'err', 'stall', 'lock', 'cti', 'bte' }
	if unknown:
		raise ValueError(f'Optional signal(s) {", ".join(map(repr, unknown))} are not supported')

class Interface(Record):
	'''
	Wishbone interface.

	See the `Wishbone specification <https://opencores.org/howto/wishbone>`_ for description
	of the Wishbone signals. The ``RST_I`` and ``CLK_I`` signals are provided as a part of
	the clock domain that drives the interface.

	Note that the data width of the underlying memory map of the interface is equal to port
	granularity, not port size. If port granularity is less than port size, then the address width
	of the underlying memory map is extended to reflect that.

	Parameters
	----------
	addr_width : int
		Width of the address signal.
	data_width : int
		Width of the data signals ("port size" in Wishbone terminology).
		One of 8, 16, 32, 64.
	granularity : int
		Granularity of select signals ("port granularity" in Wishbone terminology).
		One of 8, 16, 32, 64.
	features : iter(str)
		Selects the optional signals that will be a part of this interface.
	name : str
		Name of the underlying record.

	Attributes
	----------
	The correspondence between the Torii-SoC signals and the Wishbone signals changes depending
	on whether the interface acts as an initiator or a target.

	adr : Signal(addr_width)
		Corresponds to Wishbone signal ``ADR_O`` (initiator) or ``ADR_I`` (target).
	dat_w : Signal(data_width)
		Corresponds to Wishbone signal ``DAT_O`` (initiator) or ``DAT_I`` (target).
	dat_r : Signal(data_width)
		Corresponds to Wishbone signal ``DAT_I`` (initiator) or ``DAT_O`` (target).
	sel : Signal(data_width // granularity)
		Corresponds to Wishbone signal ``SEL_O`` (initiator) or ``SEL_I`` (target).
	cyc : Signal()
		Corresponds to Wishbone signal ``CYC_O`` (initiator) or ``CYC_I`` (target).
	stb : Signal()
		Corresponds to Wishbone signal ``STB_O`` (initiator) or ``STB_I`` (target).
	we : Signal()
		Corresponds to Wishbone signal ``WE_O``  (initiator) or ``WE_I``  (target).
	ack : Signal()
		Corresponds to Wishbone signal ``ACK_I`` (initiator) or ``ACK_O`` (target).
	err : Signal()
		Optional. Corresponds to Wishbone signal ``ERR_I`` (initiator) or ``ERR_O`` (target).
	rty : Signal()
		Optional. Corresponds to Wishbone signal ``RTY_I`` (initiator) or ``RTY_O`` (target).
	stall : Signal()
		Optional. Corresponds to Wishbone signal ``STALL_I`` (initiator) or ``STALL_O`` (target).
	lock : Signal()
		Optional. Corresponds to Wishbone signal ``LOCK_O`` (initiator) or ``LOCK_I`` (target).
		torii-soc Wishbone support assumes that initiators that don't want bus arbitration to happen in
		between two transactions need to use ``lock`` feature to guarantee this. An initiator without
		the ``lock`` feature may be arbitrated in between two transactions even if ``cyc`` is kept high.
	cti : Signal()
		Optional. Corresponds to Wishbone signal ``CTI_O`` (initiator) or ``CTI_I`` (target).
	bte : Signal()
		Optional. Corresponds to Wishbone signal ``BTE_O`` (initiator) or ``BTE_I`` (target).

	'''

	def __init__(
		self, *, addr_width: int, data_width: int, granularity: int = None,
		features: Iterable[Literal['rty', 'err', 'stall', 'lock', 'cti', 'bte']] = frozenset(),
		name: str | None = None
	) -> None:
		if granularity is None:
			granularity  = data_width

		_check_interface(addr_width, data_width, granularity, features)

		self.addr_width  = addr_width
		self.data_width  = data_width
		self.granularity = granularity
		self._map        = None

		features = set(features)
		layout = [
			('adr',   addr_width, Direction.FANOUT),
			('dat_w', data_width, Direction.FANOUT),
			('dat_r', data_width, Direction.FANIN),
			('sel',   data_width // granularity, Direction.FANOUT),
			('cyc',   1, Direction.FANOUT),
			('stb',   1, Direction.FANOUT),
			('we',    1, Direction.FANOUT),
			('ack',   1, Direction.FANIN),
		]
		if 'err' in features:
			layout += [('err', 1, Direction.FANIN)]
		if 'rty' in features:
			layout += [('rty', 1, Direction.FANIN)]
		if 'stall' in features:
			layout += [('stall', 1, Direction.FANIN)]
		if 'lock' in features:
			layout += [('lock',  1, Direction.FANOUT)]
		if 'cti' in features:
			layout += [('cti', CycleType,    Direction.FANOUT)]
		if 'bte' in features:
			layout += [('bte', BurstTypeExt, Direction.FANOUT)]
		super().__init__(layout, name = name, src_loc_at = 1)

	@property
	def memory_map(self) -> MemoryMap:
		if self._map is None:
			raise NotImplementedError(f'Bus interface {self!r} does not have a memory map')
		return self._map

	@memory_map.setter
	def memory_map(self, memory_map: MemoryMap) -> None:
		if not isinstance(memory_map, MemoryMap):
			raise TypeError(f'Memory map must be an instance of MemoryMap, not {memory_map!r}')
		if memory_map.data_width != self.granularity:
			raise ValueError(
				f'Memory map has data width {memory_map.data_width}, which is not the same as bus '
				f'interface granularity {self.granularity}'
			)
		granularity_bits = log2_exact(self.data_width // self.granularity)
		if memory_map.addr_width != max(1, self.addr_width + granularity_bits):
			raise ValueError(
				f'Memory map has address width {memory_map.addr_width}, which is not the same as bus '
				f'interface address width {self.addr_width + granularity_bits} ({self.addr_width} '
				f'address bits + {granularity_bits} granularity bits)'
			)

		memory_map.freeze()
		self._map = memory_map

class Decoder(Elaboratable):
	'''
	Wishbone bus decoder.

	An address decoder for subordinate Wishbone buses.

	Parameters
	----------
	addr_width : int
		Address width. See :class:`Interface`.
	data_width : int
		Data width. See :class:`Interface`.
	granularity : int
		Granularity. See :class:`Interface`
	features : iter(str)
		Optional signal set. See :class:`Interface`.
	alignment : log2 of int
		Window alignment. See :class:`..memory.MemoryMap`
	name : str
		Window name. Optional.

	Attributes
	----------
	bus : :class:`Interface`
		Wishbone bus providing access to subordinate buses.

	'''

	def __init__(
		self, *, addr_width: int, data_width: int, granularity: int | None = None,
		features: Iterable[Literal['rty', 'err', 'stall', 'lock', 'cti', 'bte']] = frozenset(),
		alignment: int = 0, name: str | None = None
	) -> None:
		if granularity is None:
			granularity  = data_width

		_check_interface(addr_width, data_width, granularity, features)

		self.data_width  = data_width
		self.granularity = granularity
		self.features    = set(features)
		self.alignment   = alignment

		granularity_bits = log2_exact(data_width // granularity)
		self._map        = MemoryMap(
			addr_width = max(1, addr_width + granularity_bits),
			data_width = granularity, alignment = alignment,
			name = name
		)
		self._subs       = dict()
		self._bus        = None

	@property
	def bus(self) -> Interface:
		if self._bus is None:
			self._map.freeze()
			granularity_bits = log2_exact(self.data_width // self.granularity)
			self._bus = Interface(
				addr_width = self._map.addr_width - granularity_bits,
				data_width = self.data_width, granularity = self.granularity,
				features = self.features
			)
			self._bus.memory_map = self._map
		return self._bus

	def align_to(self, alignment: int) -> int:
		'''
		Align the implicit address of the next window.

		See :meth:`MemoryMap.align_to` for details.

		'''

		return self._map.align_to(alignment)

	def add(
		self, sub_bus: Interface, *, addr: int | None = None, sparse: bool = False,
		extend: bool = False
	) -> tuple[int, int, int]:
		'''
		Add a window to a subordinate bus.

		The decoder can perform either sparse or dense address translation. If dense address
		translation is used (the default), the subordinate bus must have the same data width as
		the decoder; the window will be contiguous. If sparse address translation is used,
		the subordinate bus may have data width less than the data width of the decoder;
		the window may be discontiguous. In either case, the granularity of the subordinate bus
		must be equal to or less than the granularity of the decoder.

		See :meth:`MemoryMap.add_resource` for details.

		'''

		if not isinstance(sub_bus, Interface):
			raise TypeError(f'Subordinate bus must be an instance of wishbone.Interface, not {sub_bus!r}')
		if sub_bus.granularity > self.granularity:
			raise ValueError(
				f'Subordinate bus has granularity {sub_bus.granularity}, which is greater than the decoder '
				f'granularity {self.granularity}'
			)
		if not sparse:
			if sub_bus.data_width != self.data_width:
				raise ValueError(
					f'Subordinate bus has data width {sub_bus.data_width}, which is not the same as decoder data width '
					f'{self.data_width} (required for dense address translation)'
				)
		else:
			if sub_bus.granularity != sub_bus.data_width:
				raise ValueError(
					f'Subordinate bus has data width {sub_bus.data_width}, which is not the same as '
					f'subordinate bus granularity {sub_bus.granularity} (required for sparse address '
					'translation)'
				)
		for opt_output in { 'err', 'rty', 'stall' }:
			if hasattr(sub_bus, opt_output) and opt_output not in self.features:
				raise ValueError(
					f'Subordinate bus has optional output {opt_output!r}, but the decoder does not have '
					'a corresponding input'
				)

		self._subs[sub_bus.memory_map] = sub_bus
		return self._map.add_window(sub_bus.memory_map, addr = addr, sparse = sparse, extend = extend)

	def elaborate(self, platform) -> Module:
		m = Module()

		ack_fanin   = 0
		err_fanin   = 0
		rty_fanin   = 0
		stall_fanin = 0

		with m.Switch(self.bus.adr):
			for sub_map, (sub_pat, sub_ratio) in self._map.window_patterns():
				sub_bus = self._subs[sub_map]

				m.d.comb += [
					sub_bus.adr.eq(self.bus.adr << log2_exact(sub_ratio)),
					sub_bus.dat_w.eq(self.bus.dat_w),
					sub_bus.sel.eq(Cat(sel.replicate(sub_ratio) for sel in self.bus.sel)),
					sub_bus.we.eq(self.bus.we),
					sub_bus.stb.eq(self.bus.stb),
				]
				if hasattr(sub_bus, 'lock'):
					m.d.comb += sub_bus.lock.eq(getattr(self.bus, 'lock', 0))
				if hasattr(sub_bus, 'cti'):
					m.d.comb += sub_bus.cti.eq(getattr(self.bus, 'cti', CycleType.CLASSIC))
				if hasattr(sub_bus, 'bte'):
					m.d.comb += sub_bus.bte.eq(getattr(self.bus, 'bte', BurstTypeExt.LINEAR))

				granularity_bits = log2_exact(self.bus.data_width // self.bus.granularity)
				with m.Case(sub_pat[:-granularity_bits if granularity_bits > 0 else None]):
					m.d.comb += [
						sub_bus.cyc.eq(self.bus.cyc),
						self.bus.dat_r.eq(sub_bus.dat_r),
					]
					ack_fanin |= sub_bus.ack
					if hasattr(sub_bus, 'err'):
						err_fanin |= sub_bus.err
					if hasattr(sub_bus, 'rty'):
						rty_fanin |= sub_bus.rty
					if hasattr(sub_bus, 'stall'):
						stall_fanin |= sub_bus.stall

		m.d.comb += self.bus.ack.eq(ack_fanin)
		if hasattr(self.bus, 'err'):
			m.d.comb += self.bus.err.eq(err_fanin)
		if hasattr(self.bus, 'rty'):
			m.d.comb += self.bus.rty.eq(rty_fanin)
		if hasattr(self.bus, 'stall'):
			m.d.comb += self.bus.stall.eq(stall_fanin)

		return m

class Arbiter(Elaboratable):
	'''
	Wishbone bus arbiter.

	A round-robin arbiter for initiators accessing a shared Wishbone bus.

	Parameters
	----------
	addr_width : int
		Address width. See :class:`Interface`.
	data_width : int
		Data width. See :class:`Interface`.
	granularity : int
		Granularity. See :class:`Interface`
	features : iter(str)
		Optional signal set. See :class:`Interface`.

	Attributes
	----------
	bus : :class:`Interface`
		Shared Wishbone bus.

	'''

	def __init__(
		self, *, addr_width: int, data_width: int, granularity: int | None = None,
		features: Iterable[Literal['rty', 'err', 'stall', 'lock', 'cti', 'bte']] = frozenset()
	) -> None:
		self.bus    = Interface(
			addr_width = addr_width,
			data_width = data_width,
			granularity = granularity,
			features = features
		)
		self._intrs = []

	def add(self, intr_bus: Interface) -> None:
		'''
		Add an initiator bus to the arbiter.

		The initiator bus must have the same address width and data width as the arbiter. The
		granularity of the initiator bus must be greater than or equal to the granularity of
		the arbiter.

		'''

		if not isinstance(intr_bus, Interface):
			raise TypeError(f'Initiator bus must be an instance of wishbone.Interface, not {intr_bus!r}')
		if intr_bus.addr_width != self.bus.addr_width:
			raise ValueError(
				f'Initiator bus has address width {intr_bus.addr_width}, which is not the same as arbiter '
				f'address width {self.bus.addr_width}'
			)
		if intr_bus.granularity < self.bus.granularity:
			raise ValueError(
				f'Initiator bus has granularity {intr_bus.granularity}, which is lesser than the arbiter '
				f'granularity {self.bus.granularity}'
			)
		if intr_bus.data_width != self.bus.data_width:
			raise ValueError(
				f'Initiator bus has data width {intr_bus.data_width}, which is not the same as arbiter '
				f'data width {self.bus.data_width}'
			)
		for opt_output in { 'err', 'rty' }:
			if hasattr(self.bus, opt_output) and not hasattr(intr_bus, opt_output):
				raise ValueError(
					f'Arbiter has optional output {opt_output!r}, but the initiator bus does not have '
					'a corresponding input'
				)

		self._intrs.append(intr_bus)

	def elaborate(self, platform) -> Module:
		m = Module()

		requests = Signal(len(self._intrs))
		grant    = Signal(range(len(self._intrs)))
		m.d.comb += requests.eq(Cat(intr_bus.cyc for intr_bus in self._intrs))

		bus_busy = self.bus.cyc
		if hasattr(self.bus, 'lock'):
			# If LOCK is not asserted, we also wait for STB to be de-asserted before granting bus
			# ownership to the next initiator. If we didn't, the next bus owner could receive
			# an ACK (or ERR, RTY) from the previous transaction when targeting the same
			# peripheral.
			bus_busy &= self.bus.lock | self.bus.stb

		with m.If(~bus_busy):
			with m.Switch(grant):
				for i in range(len(requests)):
					with m.Case(i):
						for pred in reversed(range(i)):
							with m.If(requests[pred]):
								m.d.sync += grant.eq(pred)
						for succ in reversed(range(i + 1, len(requests))):
							with m.If(requests[succ]):
								m.d.sync += grant.eq(succ)

		with m.Switch(grant):
			for i, intr_bus in enumerate(self._intrs):
				m.d.comb += intr_bus.dat_r.eq(self.bus.dat_r)
				if hasattr(intr_bus, 'stall'):
					intr_bus_stall = Signal(reset = 1)
					m.d.comb += intr_bus.stall.eq(intr_bus_stall)

				with m.Case(i):
					ratio = intr_bus.granularity // self.bus.granularity
					m.d.comb += [
						self.bus.adr.eq(intr_bus.adr),
						self.bus.dat_w.eq(intr_bus.dat_w),
						self.bus.sel.eq(Cat(sel.replicate(ratio) for sel in intr_bus.sel)),
						self.bus.we.eq(intr_bus.we),
						self.bus.stb.eq(intr_bus.stb),
					]
					m.d.comb += self.bus.cyc.eq(intr_bus.cyc)
					if hasattr(self.bus, 'lock'):
						m.d.comb += self.bus.lock.eq(getattr(intr_bus, 'lock', 0))
					if hasattr(self.bus, 'cti'):
						m.d.comb += self.bus.cti.eq(getattr(intr_bus, 'cti', CycleType.CLASSIC))
					if hasattr(self.bus, 'bte'):
						m.d.comb += self.bus.bte.eq(getattr(intr_bus, 'bte', BurstTypeExt.LINEAR))

					m.d.comb += intr_bus.ack.eq(self.bus.ack)
					if hasattr(intr_bus, 'err'):
						m.d.comb += intr_bus.err.eq(getattr(self.bus, 'err', 0))
					if hasattr(intr_bus, 'rty'):
						m.d.comb += intr_bus.rty.eq(getattr(self.bus, 'rty', 0))
					if hasattr(intr_bus, 'stall'):
						m.d.comb += intr_bus_stall.eq(getattr(self.bus, 'stall', ~self.bus.ack))

		return m
