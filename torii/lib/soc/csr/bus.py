# SPDX-License-Identifier: BSD-2-Clause

from __future__      import annotations

from collections     import defaultdict
from collections.abc import Generator
from enum            import Enum

from ....build       import Platform
from ....hdl.ast     import Mux, Operator, Signal
from ....hdl.dsl     import Module
from ....hdl.ir      import Elaboratable
from ....hdl.rec     import Record
from ....util.units  import log2_ceil
from ...mem.map      import MemoryMap

__all__ = (
	'Decoder',
	'Element',
	'Interface',
	'Multiplexer',
)

class Element(Record):
	class Access(Enum):
		'''
		Register access mode.

		Coarse access mode for the entire register. Individual fields can have more restrictive
		access mode, e.g. R/O fields can be a part of an R/W register.

		'''

		R  = 'r'
		W  = 'w'
		RW = 'rw'

		def readable(self) -> bool:
			return self == self.R or self == self.RW

		def writable(self) -> bool:
			return self == self.W or self == self.RW

	r_data: Signal
	r_stb: Signal
	w_data: Signal
	w_stb: Signal
	name: str

	'''
	Peripheral-side CSR interface.

	A low-level interface to a single atomically readable and writable register in a peripheral.
	This interface supports any register width and semantics, provided that both reads and writes
	always succeed and complete in one cycle.

	Parameters
	----------
	width : int
		Width of the register.
	access : :class:`Access`
		Register access mode.
	name : str
		Name of the underlying record.

	Attributes
	----------
	r_data : Signal(width)
		Read data. Must be always valid, and is sampled when ``r_stb`` is asserted.
	r_stb : Signal()
		Read strobe. Registers with read side effects should perform the read side effect when this
		strobe is asserted.
	w_data : Signal(width)
		Write data. Valid only when ``w_stb`` is asserted.
	w_stb : Signal()
		Write strobe. Registers should update their value or perform the write side effect when
		this strobe is asserted.

	'''

	def __init__(
		self, width: int, access: Access, *, name: str | None = None, src_loc_at: int = 0
	) -> None:
		if not isinstance(width, int) or width < 0:
			raise ValueError(f'Width must be a non-negative integer, not {width!r}')
		if not isinstance(access, Element.Access) and access not in ('r', 'w', 'rw'):
			raise ValueError(f'Access mode must be one of \'r\', \'w\', or \'rw\', not {access!r}')
		self.width  = width
		self.access = Element.Access(access)

		layout = []
		if self.access.readable():
			layout += [
				('r_data', width),
				('r_stb',  1),
			]
		if self.access.writable():
			layout += [
				('w_data', width),
				('w_stb',  1),
			]
		super().__init__(layout, name = name, src_loc_at = 1 + src_loc_at)

		if self.name is None:
			AssertionError('CSR name could not be computed and must be specified')

class Interface(Record):
	'''
	CPU-side CSR interface.

	A low-level interface to a set of atomically readable and writable peripheral CSR registers.

	Operation
	---------

	CSR registers mapped to the CSR bus are split into chunks according to the bus data width.
	Each chunk is assigned a consecutive address on the bus. This allows accessing CSRs of any
	size using any datapath width.

	When the first chunk of a register is read, the value of a register is captured, and reads
	from subsequent chunks of the same register return the captured values. When any chunk except
	the last chunk of a register is written, the written value is captured; a write to the last
	chunk writes the captured value to the register. This allows atomically accessing CSRs larger
	than datapath width.

	Parameters
	----------
	addr_width : int
		Address width. At most ``(2 ** addr_width) * data_width`` register bits will be available.
	data_width : int
		Data width. Registers are accessed in ``data_width`` sized chunks.
	name : str
		Name of the underlying record.

	Attributes
	----------
	memory_map : MemoryMap
		Map of the bus.
	addr : Signal(addr_width)
		Address for reads and writes.
	r_data : Signal(data_width)
		Read data. Valid on the next cycle after ``r_stb`` is asserted. Otherwise, zero. (Keeping
		read data of an unused interface at zero simplifies multiplexers.)
	r_stb : Signal()
		Read strobe. If ``addr`` points to the first chunk of a register, captures register value
		and causes read side effects to be performed (if any). If ``addr`` points to any chunk
		of a register, latches the captured value to ``r_data``. Otherwise, latches zero
		to ``r_data``.
	w_data : Signal(data_width)
		Write data. Must be valid when ``w_stb`` is asserted.
	w_stb : Signal()
		Write strobe. If ``addr`` points to the last chunk of a register, writes captured value
		to the register and causes write side effects to be performed (if any). If ``addr`` points
		to any chunk of a register, latches ``w_data`` to the captured value. Otherwise, does
		nothing.

	'''

	addr: Signal
	r_data: Signal
	r_stb: Signal
	w_data: Signal
	w_stb: Signal

	def __init__(self, *, addr_width: int, data_width: int, name: str | None = None) -> None:
		if not isinstance(addr_width, int) or addr_width <= 0:
			raise ValueError(f'Address width must be a positive integer, not {addr_width!r}')
		if not isinstance(data_width, int) or data_width <= 0:
			raise ValueError(f'Data width must be a positive integer, not {data_width!r}')
		self.addr_width             = addr_width
		self.data_width             = data_width
		self._map: MemoryMap | None = None

		super().__init__([
			('addr',    addr_width),
			('r_data',  data_width),
			('r_stb',   1),
			('w_data',  data_width),
			('w_stb',   1),
		], name = name, src_loc_at = 1)

	@property
	def memory_map(self) -> MemoryMap:
		if self._map is None:
			raise NotImplementedError(f'Bus interface {self!r} does not have a memory map')
		return self._map

	@memory_map.setter
	def memory_map(self, memory_map: MemoryMap) -> None:
		if not isinstance(memory_map, MemoryMap):
			raise TypeError(f'Memory map must be an instance of MemoryMap, not {memory_map!r}')
		if memory_map.addr_width != self.addr_width:
			raise ValueError(
				f'Memory map has address width {memory_map.addr_width}, '
				f'which is not the same as bus interface address width {self.addr_width}'
			)
		if memory_map.data_width != self.data_width:
			raise ValueError(
				f'Memory map has data width {memory_map.data_width}, '
				f'which is not the same as bus interface data width {self.data_width}'
			)
		memory_map.freeze()
		self._map = memory_map

class Multiplexer(Elaboratable):
	class _Shadow:
		class Chunk:
			data: Signal
			r_en: Signal
			w_en: Signal

			'''The interface between a CSR multiplexer and a shadow register chunk.'''
			def __init__(self, shadow: Multiplexer._Shadow, offset: int, elements: list[range]) -> None:
				self.name = f'{shadow.name}__{offset}'
				self.data = Signal(shadow.granularity, name = f'{self.name}__data')
				self.r_en = Signal(name = f'{self.name}__r_en')
				self.w_en = Signal(name = f'{self.name}__w_en')
				self._elements = tuple(elements)

			def elements(self) -> Generator[range]:
				'''Iterate the address ranges of CSR elements using this chunk.'''
				yield from self._elements

		'''
		CSR multiplexer shadow register.

		Attributes
		----------
		name : :class:`str`
			Name of the shadow register.
		granularity : :class:`int`
			Amount of bits stored in a chunk of the shadow register.
		overlaps : :class:`int`
			Maximum number of CSR elements that can share a chunk of the shadow register. Optional.
			If ``None``, it is implicitly set by :meth:`Multiplexer._Shadow.prepare`.
		'''
		def __init__(self, granularity: int, overlaps: int | None, *, name: str) -> None:
			assert isinstance(name, str)
			assert isinstance(granularity, int) and granularity >= 0
			assert overlaps is None or isinstance(overlaps, int) and overlaps >= 0
			self.name                                                 = name
			self.granularity                                          = granularity
			self.overlaps                                             = overlaps
			self._ranges: set[range] | frozenset[range]               = set()
			self._size                                                = 1
			self._chunks: dict[int, Multiplexer._Shadow.Chunk] | None = None

		@property
		def size(self) -> int:
			'''
			Size of the shadow register.

			Returns
			-------
			:class:`int`
				The amount of :class:`Multiplexer._Shadow.Chunk`s of the shadow. It can increase
				by calling :meth:`Multiplexer._Shadow.add` or :meth:`Multiplexer._Shadow.prepare`.
			'''
			return self._size

		def add(self, elem_range: range) -> None:
			'''
			Add a CSR element to the shadow.

			Arguments
			---------
			elem_range : :class:`range`
				Address range of a CSR :class:`Element`. It uses ``2 ** log2_ceil(elem_range.stop -
				elem_range.start)`` chunks of the shadow register. If this amount is greater than
				:attr:`~Multiplexer._Shadow.size`, it replaces the latter.
			'''
			assert isinstance(elem_range, range)
			assert isinstance(self._ranges, set)
			self._ranges.add(elem_range)
			elem_size  = 2 ** log2_ceil(elem_range.stop - elem_range.start)
			self._size = max(self._size, elem_size)

		def decode_address(self, addr: int, elem_range: range) -> int:
			'''
			Decode a bus address into a shadow register offset.

			Returns
			-------
			:class:`int`
				The shadow register offset corresponding to the :class:`Multiplexer._Shadow.Chunk`
				used by ``addr``.

				The address decoding scheme is illustrated by the following example:
					* ``addr`` is ``0x1c``;
					* ``elem_range`` is ``range(0x1b, 0x1f)``;
					* the :attr:`~Multiplexer._Shadow.size` of the shadow is ``16``.

				The lower bits of the offset would be ``0b00``, extracted from ``addr``:

				.. code-block::

					+----+--+--+
					|0001|11|00|
					+----+--+--+
							│  └─ 0
							└──── log2_ceil(elem_range.stop - elem_range.start)

				The upper bits of the offset would be ``0b10``, extracted from ``elem_range.start``:

				.. code-block::

					+----+--+--+
					|0001|10|11|
					+----+--+--+
						 │  │
						 │  └──── log2_ceil(elem_range.stop - elem_range.start)
						 └─────── log2(self.size)

				The decoded offset would therefore be ``8`` (i.e. ``0b1000``).
			''' # noqa: E101
			assert elem_range in self._ranges and addr in elem_range
			elem_size: int = 2 ** log2_ceil(elem_range.stop - elem_range.start)
			self_mask = self.size - 1
			elem_mask = elem_size - 1
			return elem_range.start & self_mask & ~elem_mask | addr & elem_mask

		def encode_offset(self, offset: int, elem_range: range) -> int:
			'''
			Encode a shadow register offset into a bus address.

			Returns
			-------
			:class:`int`
				The bus address in ``elem_range`` using the :class:`Multiplexer._Shadow.Chunk`
				located at ``offset``. See :meth:`~Multiplexer._Shadow.decode_address` for details.
			'''
			assert elem_range in self._ranges and isinstance(offset, int)
			elem_size = 2 ** log2_ceil(elem_range.stop - elem_range.start)
			return elem_range.start + ((offset - elem_range.start) % elem_size)

		def prepare(self) -> None:
			'''
			Balance out and instantiate the shadow register chunks.

			The scheme used by :meth:`~Multiplexer._Shadow.decode_address` allows multiple bus
			addresses to be decoded to the same shadow register offset. Depending on the platform
			and its toolchain, this may create nets with high fan-in (if the chunk is read from
			the bus) or fan-out (if written), which may impact timing closure or resource usage.

			If any shadow register offset is aliased to more bus addresses than permitted by the
			:attr:`~Multiplexer._Shadow.overlaps` constraint, the :attr:`~Multiplexer._Shadow.size`
			of the shadow is doubled. This increases the number of address bits used for decoding,
			which effectively balances chunk usage across the shadow register.

			This method is recursive until the overlap constraint is satisfied.
			'''
			if isinstance(self._ranges, frozenset):
				return
			if self.overlaps is None:
				self.overlaps = len(self._ranges)

			elements: defaultdict[int, list[range]] = defaultdict(list)
			balanced = True

			for elem_range in self._ranges:
				for chunk_addr in elem_range:
					chunk_offset = self.decode_address(chunk_addr, elem_range)
					if len(elements[chunk_offset]) > self.overlaps:
						balanced = False
						break
					elements[chunk_offset].append(elem_range)

			if balanced:
				self._ranges = frozenset(self._ranges)
				self._chunks = {}
				for chunk_offset, chunk_elements in elements.items():
					chunk = Multiplexer._Shadow.Chunk(self, chunk_offset, chunk_elements)
					self._chunks[chunk_offset] = chunk
			else:
				self._size *= 2
				self.prepare()

		def chunks(self) -> Generator[tuple[int, Chunk]]:
			'''Iterate shadow register chunks used by at least one CSR element.'''
			if self._chunks is None:
				return None
			yield from self._chunks.items()

	'''
	CSR register multiplexer.

	An address-based multiplexer for CSR registers implementing atomic updates.

	This implementation assumes the following from the CSR bus:
	* an initiator must have exclusive ownership over the multiplexer for the full duration of
		a register transaction;
	* an initiator must access a register in ascending order of addresses, but it may abort a
		transaction after any bus cycle.

	Latency
	-------

	Writes are registered, and are performed 1 cycle after ``w_stb`` is asserted.

	Alignment
	---------

	Because the CSR bus conserves logic and routing resources, it is common to e.g. access
	a CSR bus with an *n*-bit data path from a CPU with a *k*-bit datapath (*k>n*) in cases
	where CSR access latency is less important than resource usage. In this case, two strategies
	are possible for connecting the CSR bus to the CPU:

		* The CPU could access the CSR bus directly (with no intervening logic other than simple
		  translation of control signals). In this case, the register alignment should be set
		  to 1 (i.e. `alignment` should be set to 0), and each *w*-bit register would occupy
		  *ceil(w/n)* addresses from the CPU perspective, requiring the same amount of memory
		  instructions to access.
		* The CPU could also access the CSR bus through a width down-converter, which would issue
		  *k/n* CSR accesses for each CPU access. In this case, the register alignment should be
		  set to *k/n*, and each *w*-bit register would occupy *ceil(w/k)* addresses from the CPU
		  perspective, requiring the same amount of memory instructions to access.

	If the register alignment (i.e. `2 ** alignment`) is greater than 1, it affects which CSR bus
	write is considered a write to the last register chunk. For example, if a 24-bit register is
	used with a 8-bit CSR bus and a CPU with a 32-bit datapath, a write to this register requires
	4 CSR bus writes to complete and the 4th write is the one that actually writes the value to
	the register. This allows determining write latency solely from the amount of addresses the
	register occupies in the CPU address space, and the width of the CSR bus.

	Parameters
	----------
	addr_width : int
		Address width. See :class:`Interface`.
	data_width : int
		Data width. See :class:`Interface`.
	alignment : log2 of int
		Register alignment. See :class:`..memory.MemoryMap`.
	name : str
		Window name. Optional.

	shadow_overlaps : int
		Maximum number of CSR registers that can share a chunk of a shadow register.
		Optional. If ``None``, any number of CSR registers can share a shadow chunk.
		See :class:`Multiplexer._Shadow` for details.

	Attributes
	----------
	bus : :class:`Interface`
		CSR bus providing access to registers.

	''' # noqa: E101

	def __init__(
		self, *, addr_width: int, data_width: int, alignment: int = 0, name: str | None = None,
		shadow_overlaps: int | None = None
	) -> None:
		self._map = MemoryMap(
			addr_width = addr_width, data_width = data_width,
			alignment = alignment, name = name
		)
		self._bus: Interface | None = None
		self._r_shadow              = Multiplexer._Shadow(data_width, shadow_overlaps, name = 'r_shadow')
		self._w_shadow              = Multiplexer._Shadow(data_width, shadow_overlaps, name = 'w_shadow')

	@property
	def bus(self) -> Interface:
		if self._bus is None:
			self._map.freeze()
			self._bus = Interface(
				addr_width = self._map.addr_width,
				data_width = self._map.data_width,
				name = 'csr'
			)
			self._bus.memory_map = self._map
		return self._bus

	def align_to(self, alignment: int) -> int:
		'''
		Align the implicit address of the next register.

		See :meth:`MemoryMap.align_to` for details.

		'''

		return self._map.align_to(alignment)

	def add(
		self, element: Element, *, addr: int | None = None, alignment: int | None = None,
		extend: bool = False
	) -> tuple[int, int]:
		'''
		Add a register.

		See :meth:`MemoryMap.add_resource` for details.

		'''

		if not isinstance(element, Element):
			raise TypeError(f'Element must be an instance of csr.Element, not {element!r}')

		size = (element.width + self._map.data_width - 1) // self._map.data_width
		return self._map.add_resource(
			element, size = size, addr = addr, alignment = alignment,
			extend = extend, name = element.name
		)

	def elaborate(self, platform: Platform | None) -> Module:
		m = Module()

		for elem, _, (elem_start, elem_end) in self._map.resources():
			assert isinstance(elem, Element)
			elem_range = range(elem_start, elem_end)
			if elem.access.readable():
				self._r_shadow.add(elem_range)
			if elem.access.writable():
				self._w_shadow.add(elem_range)

		self._r_shadow.prepare()
		self._w_shadow.prepare()

		# Instead of a straightforward multiplexer for reads, use a per-element address comparator,
		# AND the shadow register chunk with the comparator output, and OR all of those together.
		# If the toolchain doesn't already synthesize multiplexer trees this way, this trick can
		# save a significant amount of logic, since e.g. one 4-LUT can pack one 2-MUX, but two
		# 2-AND or 2-OR gates.
		r_data_fanin: int | Operator = 0

		for chunk_offset, r_chunk, in self._r_shadow.chunks():
			# Use the same trick to select which element is read into a shadow register chunk.
			r_chunk_w_en_fanin: int | Operator = 0
			r_chunk_data_fanin: int | Operator = 0

			m.d.sync += r_chunk.r_en.eq(0)

			with m.Switch(self.bus.addr):
				for elem_range in r_chunk.elements():
					chunk_addr  = self._r_shadow.encode_offset(chunk_offset, elem_range)
					elem        = self._map.decode_address(elem_range.start)
					assert isinstance(elem, Element)
					elem_offset = chunk_addr - elem_range.start
					elem_slice  = elem.r_data.word_select(elem_offset, self.bus.data_width)

					with m.Case(chunk_addr):
						if chunk_addr == elem_range.start:
							m.d.comb += elem.r_stb.eq(self.bus.r_stb)
						# Delay by 1 cycle, allowing reads to be pipelined.
						m.d.sync += r_chunk.r_en.eq(self.bus.r_stb)

					r_chunk_w_en_fanin |= elem.r_stb
					r_chunk_data_fanin |= Mux(elem.r_stb, elem_slice, 0)

			m.d.comb += r_chunk.w_en.eq(r_chunk_w_en_fanin)
			with m.If(r_chunk.w_en):
				m.d.sync += r_chunk.data.eq(r_chunk_data_fanin)

			r_data_fanin |= Mux(r_chunk.r_en, r_chunk.data, 0)

		m.d.comb += self.bus.r_data.eq(r_data_fanin)

		for chunk_offset, w_chunk in self._w_shadow.chunks():
			with m.Switch(self.bus.addr):
				for elem_range in w_chunk.elements():
					chunk_addr  = self._w_shadow.encode_offset(chunk_offset, elem_range)
					elem        = self._map.decode_address(elem_range.start)
					assert isinstance(elem, Element)
					elem_offset = chunk_addr - elem_range.start
					elem_slice  = elem.w_data.word_select(elem_offset, self.bus.data_width)

					if chunk_addr == elem_range.stop - 1:
						m.d.sync += elem.w_stb.eq(0)

					with m.Case(chunk_addr):
						if chunk_addr == elem_range.stop - 1:
							# Delay by 1 cycle, avoiding combinatorial paths through
							# the CSR bus and into CSR registers.
							m.d.sync += elem.w_stb.eq(self.bus.w_stb)
						m.d.comb += w_chunk.w_en.eq(self.bus.w_stb)

					m.d.comb += elem_slice.eq(w_chunk.data)

			with m.If(w_chunk.w_en):
				m.d.sync += w_chunk.data.eq(self.bus.w_data)

		return m

class Decoder(Elaboratable):
	'''
	CSR bus decoder.

	An address decoder for subordinate CSR buses.

	Usage
	-----

	Although there is no functional difference between adding a set of registers directly to
	a :class:`Multiplexer` and adding a set of registers to multiple :class:`Multiplexer`s that are
	aggregated with a :class:`Decoder`, hierarchical CSR buses are useful for organizing
	a hierarchical design. If many peripherals are directly served by a single
	:class:`Multiplexer`, a very large amount of ports will connect the peripheral registers with
	the decoder, and the cost of decoding logic would not be attributed to specific peripherals.
	With a decoder, only five signals per peripheral will be used, and the logic could be kept
	together with the peripheral.

	Parameters
	----------
	addr_width : int
		Address width. See :class:`Interface`.
	data_width : int
		Data width. See :class:`Interface`.
	alignment : log2 of int
		Window alignment. See :class:`..memory.MemoryMap`.
	name : str
		Window name. Optional.

	Attributes
	----------
	bus : :class:`Interface`
		CSR bus providing access to subordinate buses.

	'''

	def __init__(
		self, *, addr_width: int, data_width: int, alignment: int = 0, name: str | None = None
	) -> None:
		self._map  = MemoryMap(
			addr_width = addr_width, data_width = data_width,
			alignment = alignment, name = name,
		)
		self._bus: Interface | None            = None
		self._subs: dict[MemoryMap, Interface] = {}

	@property
	def bus(self) -> Interface:
		if self._bus is None:
			self._map.freeze()
			self._bus = Interface(
				addr_width = self._map.addr_width,
				data_width = self._map.data_width,
				name = 'csr'
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
		self, sub_bus: Interface, *, addr: int | None = None, extend: bool = False
	) -> tuple[int, int, int]:
		'''
		Add a window to a subordinate bus.

		See :meth:`MemoryMap.add_resource` for details.

		'''

		if not isinstance(sub_bus, Interface):
			raise TypeError(f'Subordinate bus must be an instance of csr.Interface, not {sub_bus!r}')
		if sub_bus.data_width != self._map.data_width:
			raise ValueError(
				f'Subordinate bus has data width {sub_bus.data_width}, '
				f'which is not the same as decoder data width {self._map.data_width}'
			)
		self._subs[sub_bus.memory_map] = sub_bus
		return self._map.add_window(sub_bus.memory_map, addr = addr, extend = extend)

	def elaborate(self, _: Platform | None) -> Module:
		m = Module()

		# See Multiplexer.elaborate above.
		r_data_fanin: int | Operator = 0

		with m.Switch(self.bus.addr):
			for sub_map, (sub_pat, sub_ratio) in self._map.window_patterns():
				if sub_ratio != 1:
					raise ValueError(f'sub_ratio must be exactly 1, not {sub_ratio}')

				sub_bus = self._subs[sub_map]
				m.d.comb += sub_bus.addr.eq(self.bus.addr[:sub_bus.addr_width])

				# The CSR bus interface is defined to output zero when idle, allowing us to avoid
				# adding a multiplexer here.
				r_data_fanin |= sub_bus.r_data
				m.d.comb += sub_bus.w_data.eq(self.bus.w_data)

				with m.Case(sub_pat):
					m.d.comb += sub_bus.r_stb.eq(self.bus.r_stb)
					m.d.comb += sub_bus.w_stb.eq(self.bus.w_stb)

		m.d.comb += self.bus.r_data.eq(r_data_fanin)

		return m
